class Push:
    def __init__(self, ref: str, event: str, args: dict, channel, *, timeout: float = 10) -> None:
        self.ref = ref
        self.event = event
        self.args = args
        self.channel = channel
        self.timeout = timeout
        self._handlers = {}
        self.channel.socket._push(self.channel.topic, event, args, ref, self.channel._join_ref)

    def receive(self, event):
        def handler(func):
            self._handlers[event] = func
        return handler

    def _on_message(self, message):
        if message["join_ref"] == self.channel._join_ref and message["ref"] == self.ref and message["topic"] == self.channel.topic and message["event"] == "phx_reply":
            if message["payload"]["status"] == "ok":
                if "ok" in self._handlers:
                    self._handlers["ok"](message["payload"]["response"])
            elif message["payload"]["status"] == "error":
                if "error" in self._handlers:
                    self._handlers["error"](message["payload"]["response"])
