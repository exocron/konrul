from .push import Push


class Channel:
    def __init__(self, topic: str, args: dict, socket) -> None:
        self.topic = topic
        self.args = args
        self.socket = socket
        self._join_ref = None
        self._events = {}

    def join(self) -> None:
        if self._join_ref is None:
            self._join_ref = self.socket.ref()
            self.socket._push(self.topic, "phx_join", self.args, self._join_ref, self._join_ref)

    def _on_message(self, message: dict) -> None:
        if message["topic"] == self.topic:
            if message["join_ref"] == self._join_ref or message["join_ref"] is None:
                if message["ref"] is None and message["event"] in self._events:
                    self._events[message["event"]](message)

    def push(self, event: str, args: dict, *, timeout: float = 10) -> None:
        push = Push(event, args, self, timeout=timeout)
        return push

    def on(self, event):
        def handler(func):
            self._events[event] = func
        return handler
