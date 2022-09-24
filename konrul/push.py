class Push:
    def __init__(self, topic: str, event: str, args: dict, channel, *, timeout: float = 10) -> None:
        self.topic = topic
        self.event = event
        self.args = args
        self.channel = channel
        self.timeout = timeout
