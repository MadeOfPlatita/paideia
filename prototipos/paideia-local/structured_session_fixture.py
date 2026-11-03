"""Closed in-memory transport for explicitly assembled synthetic sessions only.

This fixture is not a sandbox against code that can alter Python process state.
The request log and legacy sequence mirror do not control outcome progression.
"""
from providers import TransportResponse
import threading

_LOCK_TYPE = type(threading.Lock())

class StructuredSessionFixture:
    __slots__ = ('status', 'body', 'requests', 'connect_entered', 'connect_release', 'post_entered', 'post_release', '_outcomes', '_sequence', '_sequence_lock', '_sequence_counter')
    test_only = True

    def __init__(self, status, body, *, outcomes=None):
        if type(status) is not int or type(body) is not bytes or not valid_outcomes(outcomes):
            raise ValueError('invalid fixture')
        self._outcomes = outcomes
        self._sequence = 0
        self._sequence_counter = [0]
        self._sequence_lock = threading.Lock()
        self.status, self.body, self.requests = status, body, []
        self.connect_entered = self.connect_release = None
        self.post_entered = self.post_release = None

    def post(self, *, host, path, headers, body, timeout, send_guard):
        status, response, requests = self.status, self.body, self.requests
        entered, release = self.connect_entered, self.connect_release
        posted, post_release = self.post_entered, self.post_release
        outcomes = self._outcomes
        lock = self._sequence_lock
        counter = self._sequence_counter
        if type(counter) is not list:
            raise ValueError('invalid sequence counter')
        if type(lock) is not _LOCK_TYPE:
            raise ValueError('invalid sequence lock')
        if type(status) is not int or type(response) is not bytes or type(requests) is not list or type(body) is not bytes or not valid_outcomes(outcomes):
            raise ValueError('invalid fixture state')
        for a, b in ((entered, release), (posted, post_release)):
            if (a is not None or b is not None) and (type(a) is not threading.Event or type(b) is not threading.Event):
                raise ValueError('invalid synchronization fixture')
        if entered is not None:
            threading.Event.set(entered)
            if not threading.Event.wait(release, 3):
                raise TimeoutError('synthetic connect timeout')
        with send_guard():
            _LOCK_TYPE.acquire(lock)
            try:
                if len(counter) != 1 or type(counter[0]) is not int or counter[0] < 0:
                    raise ValueError('invalid sequence counter')
                index = counter[0]
                counter[0] = index + 1
                self._sequence = index + 1
                list.append(requests, body)
                if outcomes is not None:
                    if index >= len(outcomes):
                        raise ValueError('fixture outcomes exhausted')
                    status, response = outcomes[index]
            finally:
                _LOCK_TYPE.release(lock)
        if posted is not None:
            threading.Event.set(posted)
            if not threading.Event.wait(post_release, 3):
                raise TimeoutError('synthetic response timeout')
        return TransportResponse(status, response)

def valid_outcomes(outcomes):
    return outcomes is None or (type(outcomes) is tuple and bool(outcomes) and all(
        type(item) is tuple and len(item) == 2 and type(item[0]) is int and type(item[1]) is bytes for item in outcomes))

fixture_post = StructuredSessionFixture.post
