import asyncio
import json
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from .channel import Channel
from .transport.websocket import ReconnectingWebsocket


class Socket:

    class Impl(ReconnectingWebsocket):
        def __init__(self, uri: str, parent) -> None:
            super().__init__(uri)
            self.parent = parent

        def on_message(self, message: str) -> None:
            self.parent._on_message(message)

        def on_open(self) -> None:
            self.parent._on_open()

    def __init__(self, uri: str, args: dict) -> None:
        uri = urlparse(uri)
        if not uri.scheme or not uri.netloc or not uri.path.startswith("/"):
            raise Exception("relative URLs are not allowed")
        if uri.scheme == "http":
            uri = uri._replace(scheme="ws")
        elif uri.scheme == "https":
            uri = uri._replace(scheme="wss")
        if uri.scheme not in ("ws", "wss"):
            raise Exception(f"unknown scheme {uri.scheme}, expected ws or wss")
        if uri.path.endswith("/"):
            uri = uri._replace(path=uri.path + "websocket")
        else:
            uri = uri._replace(path=uri.path + "/websocket")
        if uri.query:
            print("Warning: query parameters were included in the socket URL; consider using the args parameter instead")
            query = {k: v[0] for k, v in parse_qs(uri.query).items()}
        else:
            query = {}
        query.update(args)
        query["vsn"] = "2.0.0"
        query = urlencode(query)
        uri = uri._replace(query=query)
        uri = urlunparse(uri)
        self.uri = uri
        self.conn = None
        self._ref = 1
        self._channels = {}
        self._queue = []

    def connect(self) -> None:
        if self.conn is None:
            self.conn = self.Impl(self.uri, self)

    def _on_message(self, message: str) -> None:
        join_ref, ref, topic, event, payload = json.loads(message)
        if topic in self._channels:
            c = self._channels[topic]
            if join_ref is None or c._join_ref == join_ref:
                c._on_message({"join_ref": join_ref, "ref": ref, "topic": topic, "event": event, "payload": payload})

    def _on_open(self) -> None:
        for message in self._queue:
            self.conn.send(message)
        self._queue = []

    def channel(self, topic: str, args: dict = {}):
        channel = Channel(topic, args, self)
        if topic in self._channels:
            self._channels.leave()
            del self._channels[topic]
        self._channels[topic] = channel
        return channel

    def _push(self, topic: str, event: str, payload: dict, ref: str = None, join_ref: str = None) -> None:
        data = json.dumps([join_ref, ref, topic, event, payload])
        if self._is_connected():
            self.conn.send(data)
        else:
            self._queue.append(data)

    def ref(self) -> str:
        ref = self._ref
        self._ref += 1
        return str(ref)

    def _is_connected(self):
        return self.conn is not None and self.conn.is_connected()
