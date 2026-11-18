"""A stand-in for owserver in the tests: started by the app like the real one.

    fake_owserver.py --foreground ... -u -p 127.0.0.1:<port>

FAKE_OWSERVER_MODE: "" answers like an owserver with a sensor and the adapter's ID chip,
"hang" takes connections and never answers (a DS2490 that stopped), "fail" ends at once with
exit code 1. Every start appends its arguments to FAKE_OWSERVER_LOG, if set.
"""

import asyncio
import os
import struct
import sys

HEADER = struct.Struct(">iiiiii")
DIRALL = b"/28.A1B2C3D4E5F6,/81.0000005F2A1B,/bus.0,/settings\0"


async def serve(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    mode = os.environ.get("FAKE_OWSERVER_MODE", "")
    try:
        head = await reader.readexactly(HEADER.size)
        _version, payload, kind, _flags, _size, _offset = HEADER.unpack(head)
        await reader.readexactly(payload)
        if mode == "hang":
            await asyncio.sleep(3600)
        body = DIRALL if kind == 7 else b"     21.5"
        writer.write(HEADER.pack(0, len(body), len(body) if kind != 7 else 0, 0, len(body), 0))
        writer.write(body)
        await writer.drain()
    except asyncio.IncompleteReadError:
        pass
    writer.close()


async def main() -> None:
    if log := os.environ.get("FAKE_OWSERVER_LOG"):
        with open(log, "a", encoding="utf-8") as f:
            f.write(" ".join(sys.argv[1:]) + "\n")
    if os.environ.get("FAKE_OWSERVER_MODE") == "fail":
        print("DEFAULT: ow_usb_msg.c:(199) Could not open the USB adapter", flush=True)
        sys.exit(1)
    host, port = sys.argv[sys.argv.index("-p") + 1].rsplit(":", 1)
    server = await asyncio.start_server(serve, host, int(port))
    print("owserver ready", flush=True)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
