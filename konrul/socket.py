import asyncio
import json
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

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
        self.conn = self.Impl(uri, self)
        self._ref = 1

    def _on_message(self, message: str) -> None:
        print(f"received message: {message}")

    def _on_open(self) -> None:
        pass

    def push(self, message: dict) -> None:
        pass

    def ref(self) -> str:
        ref = self._ref
        self._ref += 1
        return str(ref)
