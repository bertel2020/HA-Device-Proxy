"""A stand-in for owhttpd in the tests: started by the app like the real one.

    fake_owhttpd.py --foreground ... -s 127.0.0.1:<owserver> -p 127.0.0.1:<port> [--readonly]

Answers GET /<path> with the value the owserver reads for it (one owserver request each, as
owhttpd sends them), a path with "?" (a write in owhttpd's forms) with 403 when read only.
Every start appends its arguments to FAKE_OWHTTPD_LOG, if set.
"""

import asyncio
import os
import struct
import sys

HEADER = struct.Struct(">iiiiii")


async def read_value(server: str, path: str) -> tuple[int, bytes]:
    host, port = server.rsplit(":", 1)
    reader, writer = await asyncio.open_connection(host, int(port))
    payload = path.encode() + b"\0"
    writer.write(HEADER.pack(0, len(payload), 2, 0, 8192, 0) + payload)
    head = await reader.readexactly(HEADER.size)
    _version, length, ret, _flags, _size, _offset = HEADER.unpack(head)
    body = await reader.readexactly(max(length, 0))
    writer.close()
    return ret, body


def handler(server: str, readonly: bool):  # type: ignore[no-untyped-def]
    async def serve(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        line = await reader.readline()
        while (await reader.readline()).strip():
            pass  # the headers
        parts = line.decode().split()
        path = parts[1] if len(parts) > 1 else "/"
        if "?" in path and readonly:
            status, body = "403 Forbidden", b"read only"
        else:
            ret, value = await read_value(server, path.split("?", 1)[0])
            status, body = ("200 OK", value) if ret >= 0 else ("404 Not Found", b"")
        writer.write(f"HTTP/1.0 {status}\r\nContent-Length: {len(body)}\r\n\r\n".encode() + body)
        await writer.drain()
        writer.close()

    return serve


async def main() -> None:
    args = sys.argv[1:]
    if log := os.environ.get("FAKE_OWHTTPD_LOG"):
        with open(log, "a", encoding="utf-8") as f:
            f.write(" ".join(args) + "\n")
    server = args[args.index("-s") + 1]
    host, port = args[args.index("-p") + 1].rsplit(":", 1)
    http = await asyncio.start_server(handler(server, "--readonly" in args), host, int(port))
    print("owhttpd ready", flush=True)
    async with http:
        await http.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
