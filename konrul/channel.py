from weakref import WeakValueDictionary

from .push import Push


class Channel:
    def __init__(self, topic: str, args: dict, socket) -> None:
        self.topic = topic
        self.args = args
        self.socket = socket
        self._join_ref = None
        self._events = {}
        self._pushes = {}

    def join(self) -> None:
        if self._join_ref is None:
            self._join_ref = self.socket.ref()
            self.socket._push(self.topic, "phx_join", self.args, self._join_ref, self._join_ref)

    def _on_message(self, message: dict) -> None:
        if message["topic"] == self.topic:
            if message["event"] == "phx_reply":
                if message["ref"] == self._join_ref:
                    pass
                elif message["ref"] in self._pushes and message["join_ref"] == self._join_ref:
                    push = self._pushes[message["ref"]]
                    del self._pushes[message["ref"]]
                    push._on_message(message)
            elif message["join_ref"] == self._join_ref or message["join_ref"] is None:
                if message["ref"] is None and message["event"] in self._events:
                    self._events[message["event"]](message["payload"])

    def push(self, event: str, args: dict, *, timeout: float = 10) -> None:
        ref = self.socket.ref()
        push = Push(ref, event, args, self, timeout=timeout)
        self._pushes[ref] = push
        return push

    def on(self, event):
        def handler(func):
            self._events[event] = func
        return handler
