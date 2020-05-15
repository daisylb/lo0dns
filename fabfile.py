from fabric import task
from patchwork import files
from shlex import quote

hosts = ('root@lo0-ns1.leigh.party',)

def ensure_file(c, path, content):
    quoted_content = quote(content)
    quoted_path = quote(path)
    c.run(f"echo {quoted_content} > {quoted_path}")


UNATTENDED_UPGRADES_FILE = """
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
Unattended-Upgrade::Automatic-Reboot "true";
"""

UNIT_FILE = """
[Unit]
Description=DNS server
After=network.target

[Service]
User=dns
ExecStart=/opt/dns-venv/bin/python -m lo0dns.dns 10.69.54.103 2001:bc8:628:1b33::1
AmbientCapabilities=CAP_NET_BIND_SERVICE

[Install]
WantedBy=default.target
"""


@task(hosts=hosts)
def deploy(c):
    # setup firewall
    c.run("ufw allow ssh")
    c.run("ufw allow 53")
    c.run("ufw enable")
    c.run("ufw status verbose")

    # upgrade and setup unattended upgrades
    c.run('apt-get update')
    c.run('apt-get upgrade')
    c.run("apt-get install -y unattended-upgrades update-notifier-common")
    ensure_file(c, '/etc/apt/apt.conf.d/99-site-auto-upgrades', UNATTENDED_UPGRADES_FILE)

    # add user
    c.run('adduser --system --no-create-home --gecos "" dns')

    # install python
    c.run('add-apt-repository universe')
    c.run('apt-get install -y python3.8 python3.8-venv python3.8-dev build-essential')

    # create venv
    c.run('test -f /opt/dns-venv || python3.8 -m venv /opt/dns-venv')

    # install the project
    c.run('/opt/dns-venv/bin/pip install -U git+https://github.com/excitedleigh/lo0dns')
    ensure_file(c, '/etc/systemd/system/lo0dns.service', UNIT_FILE)
    c.run('systemctl daemon-reload')
    c.run('systemctl restart lo0dns.service')
    c.run('systemctl status lo0dns.service')

@task(hosts=hosts)
def update(c):
    c.run('systemctl stop lo0dns.service')
    c.run('/opt/dns-venv/bin/pip install -U git+https://github.com/excitedleigh/lo0dns')
    c.run('systemctl start lo0dns.service')
    c.run('systemctl status lo0dns.service')