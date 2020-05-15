from twisted.internet.defer import ensureDeferred, Deferred
import typing as t
from functools import wraps

# this will be able to be typed properly when PEP 612 is implemented
def ensure_returns_deferred(wrapped: t.Callable[..., t.Awaitable[t.Any]]) -> t.Callable[..., Deferred]:
    @wraps(wrapped)
    def outer(*args, **kwargs):
        return ensureDeferred(wrapped(*args, **kwargs))
    return outer