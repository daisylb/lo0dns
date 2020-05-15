from .util import ensure_returns_deferred
from twisted.names.dns import Query, RRHeader, Record_AAAA, AAAA, ALL_RECORDS, \
    Record_SOA, SOA
from twisted.names.error import DomainError
import typing as t
from cityhash import CityHash32
from ipaddress import IPv6Network
from time import time

NETWORK = IPv6Network('fd7f:1fa7:68ca:202f::/64')

class Resolver:
    def __init__(self, callback: t.Callable[[Query], t.Awaitable[t.List[RRHeader]]]):
        self.callback = callback
    
    @ensure_returns_deferred
    async def query(self, query, timeout=None):
        answers = await self.callback(query)
        if answers is None:
            return [], [], []
        return answers, [], []
    
    @ensure_returns_deferred
    async def lookupAllRecords(self, name, timeout=None):
        query = Query(name, type=ALL_RECORDS)
        answers = await self.callback(query)
        return answers, [], []


SOA_OBJ = RRHeader(
    name='lo0.wtf',
    type=SOA,
    ttl=60,
    payload=Record_SOA(
    mname='lo0-ns1.leigh.party',
    rname='l.leigh.net.au',
    serial=int(time() / 10),
    refresh=60,
    retry=60,
    expire=60,
    minimum=60,
))

async def get_response(query: Query):
    name = query.name.name
    if name.endswith(b'.'): name = name[:-1]
    if not name.endswith(b'.lo0.wtf'): raise DomainError()
    results = []
    if query.type in (AAAA, ALL_RECORDS):
        name = name[:-8]
        vhost, username = name.rsplit(b'.')
        vhost_hash = CityHash32(vhost)
        username_hash = CityHash32(username)
        ip = NETWORK[(username_hash << 32) + vhost_hash]
        results.append(RRHeader(
                    name=query.name.name,
                    type=AAAA,
                    ttl=60,
                    payload=Record_AAAA(address=str(ip).encode('ascii')),
                ))
    if query.type in (SOA, ALL_RECORDS):
        results.append(SOA_OBJ)
    return results


if __name__ == "__main__":
    from twisted.internet import reactor
    from twisted.names import dns, server
    from sys import argv

    resolver = Resolver(get_response)

    factory = server.DNSServerFactory(
        authorities=[resolver]
    )


    for addr in argv[1:]:
        protocol = dns.DNSDatagramProtocol(controller=factory)
        reactor.listenUDP(53, protocol, interface=addr)
        reactor.listenTCP(53, factory, interface=addr)

    reactor.run()