from publicsuffixlist import PublicSuffixList
from ipaddress import IPv6Network
from cityhash import CityHash32

NETWORK = IPv6Network('fd7f:1fa7:68ca:202f::/64')

psl = PublicSuffixList()

SHARED_DOMAINS = ('.lo0.wtf',)

def domain_to_ip(domain: str):
    if domain.endswith('.'):
        domain = domain[:-1]
    for shared_domain in SHARED_DOMAINS:
        if domain.endswith(shared_domain):
            service_part, user_part = domain[:-len(shared_domain)].rsplit('.', 1)
            user_part += shared_domain
            break
    else:
        user_part = psl.privatesuffix(domain)
        service_part = domain[:-len(user_part) - 1]
    user_hash = CityHash32(user_part.encode('ascii'))
    service_hash = CityHash32(service_part.encode('ascii'))
    return NETWORK[(user_hash << 32) + service_hash]
