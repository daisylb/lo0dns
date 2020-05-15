from .util import ensure_returns_deferred
from twisted.names.dns import Query, RRHeader, Record_AAAA, AAAA
from twisted.names.error import DomainError
import typing as t

class Resolver:
    def __init__(self, callback: t.Callable[[Query], t.Awaitable[t.List[RRHeader]]]):
        self.callback = callback
    
    @ensure_returns_deferred
    async def query(self, query, timeout=None):
        answers = await self.callback(query)
        if answers is None:
            raise DomainError()
        return answers, [], []


if __name__ == "__main__":
    from twisted.internet import reactor
    from twisted.names import dns, server
    async def get_response(query: Query):
        if query.name.name.endswith(b'.lo0.wtf'):
            return [RRHeader(
                name=query.name.name,
                type=AAAA,
                payload=Record_AAAA(address=b'::1'),
            )]
    resolver = Resolver(get_response)

    factory = server.DNSServerFactory(
        clients=[resolver]
    )

    protocol = dns.DNSDatagramProtocol(controller=factory)

    reactor.listenUDP(10053, protocol)
    reactor.listenTCP(10053, factory)

    reactor.run()