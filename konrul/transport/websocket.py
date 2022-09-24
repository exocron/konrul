import asyncio
import traceback

from websockets import connect


class CallbackWebsocket:
    def __init__(self, uri: str) -> None:
        self._ws = None
        self._task = asyncio.create_task(self._ainit(uri))
        self._write_tasks = set()

    async def _ainit(self, uri: str) -> None:
        loop = asyncio.get_event_loop()
        try:
            async with connect(uri) as ws:
                self._ws = ws
                loop.call_soon(self.on_open)
                async for message in ws:
                    loop.call_soon(self.on_message, message)
        except Exception as exc:
            loop.call_soon(self.on_error, exc)
        self._ws = None
        loop.call_soon(self.on_close)

    def send(self, message: str) -> None:
        if self._ws is None:
            raise Exception("send() called when websocket was closed")
        task = asyncio.create_task(self._ws.send(message))
        self._write_tasks.add(task)
        task.add_done_callback(self._write_tasks.discard)

    def on_close(self) -> None:
        print("websocket was closed (override this method to handle)")

    def on_error(self, exc) -> None:
        print("websocket had error (override this method to handle)")
        traceback.print_exception(exc)

    def on_message(self, message: str) -> None:
        print(f"websocket received message: {message} (override this method to handle)")

    def on_open(self) -> None:
        print("websocket was opened (override this method to handle)")

    def is_connected(self) -> bool:
        return self._ws is not None


class ReconnectingWebsocket:

    class Impl(CallbackWebsocket):
        def __init__(self, uri: str, parent) -> None:
            super().__init__(uri)
            self.parent = parent

        def on_close(self) -> None:
            self.parent._on_close()

        def on_error(self, exc) -> None:
            self.parent._on_error(exc)

        def on_message(self, message: str) -> None:
            self.parent.on_message(message)

        def on_open(self) -> None:
            self.parent._failure = 0
            self.parent.on_open()

    def __init__(self, uri: str) -> None:
        self.uri = uri
        self._ws = self.Impl(uri, self)
        self._failure = 0

    def _on_close(self) -> None:
        # delete and create new websocket object
        self._ws = None
        self._failure += 1
        if self._failure < 100:
            self._ws = self.Impl(self.uri, self)
        else:
            print("!!! 100 failures in a row, stopping !!!")
            # TODO: add delay instead of using counter

    def _on_error(self, exc) -> None:
        traceback.print_exception(exc)

    def on_message(self, message: str) -> None:
        print(f"websocket received message: {message} (override this method to handle)")

    def on_open(self) -> None:
        print("websocket was opened (override this method to handle)")

    def send(self, message: str) -> None:
        self._ws.send(message)

    def is_connected(self) -> bool:
        return self._ws is not None and self._ws.is_connected()
