# konrul

A phoenix-compatible channels client for Python.

Experimental.

-----

**Table of Contents**

- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Installation

```console
pip install git+https://github.com/exocron/konrul.git
```

## Usage

```python
from konrul.socket import Socket

socket = Socket("ws://localhost:4000/socket", {"token", "123"})
channel = socket.channel("room:123", {"token": roomToken})
channel.join()

@channel.on("new_msg")
def _(msg):
    print(f"Got message: {msg}")

push = channel.push("new_msg", {"body": "Hello, world!"})

@push.receive("ok")
def _(msg):
    print(f"Created message: {msg}")

@push.receive("error")
def _(reason):
    print(f"Create failed: {reason}")

# Call connect inside of an event loop
async def async_main():
    socket.connect()
    await asyncio.Event().wait()
asyncio.run(async_main())
```

## License

`konrul` is distributed under the terms of the [0BSD](https://spdx.org/licenses/0BSD.html) license.
