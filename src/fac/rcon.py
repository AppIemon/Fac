"""Minimal Minecraft RCON client (stdlib)."""

from __future__ import annotations

import socket
import struct
import time


TYPE_LOGIN = 3
TYPE_COMMAND = 2
TYPE_RESPONSE = 0


class RconError(RuntimeError):
    pass


class Rcon:
    def __init__(self, host: str, port: int, password: str, timeout: float = 10.0) -> None:
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
        self._req = 0
        self._sock: socket.socket | None = None

    def connect(self) -> None:
        sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        sock.settimeout(self.timeout)
        self._sock = sock
        payload = self._send(TYPE_LOGIN, self.password)
        if payload is None:
            raise RconError("login failed")

    def close(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def command(self, text: str) -> str:
        return self._send(TYPE_COMMAND, text) or ""

    def _send(self, ptype: int, body: str) -> str | None:
        assert self._sock is not None
        self._req += 1
        req = self._req
        encoded = body.encode("utf-8")
        packet = struct.pack("<ii", req, ptype) + encoded + b"\x00\x00"
        self._sock.sendall(struct.pack("<i", len(packet)) + packet)
        data = self._read_packet()
        if data is None:
            return None
        resp_id, resp_type, payload = data
        if ptype == TYPE_LOGIN and resp_id == -1:
            raise RconError("bad rcon password")
        # Some servers pad with an empty follow-up packet.
        extra = self._maybe_read()
        if extra:
            payload += extra[2]
        return payload.decode("utf-8", errors="replace")

    def _read_packet(self) -> tuple[int, int, bytes] | None:
        assert self._sock is not None
        header = _recv_exact(self._sock, 4)
        if not header:
            return None
        (length,) = struct.unpack("<i", header)
        body = _recv_exact(self._sock, length)
        req_id, ptype = struct.unpack("<ii", body[:8])
        payload = body[8:-2]
        return req_id, ptype, payload

    def _maybe_read(self) -> tuple[int, int, bytes] | None:
        assert self._sock is not None
        self._sock.settimeout(0.15)
        try:
            return self._read_packet()
        except (socket.timeout, TimeoutError, OSError):
            return None
        finally:
            self._sock.settimeout(self.timeout)


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise RconError("connection closed")
        buf += chunk
    return buf


def wait_for_port(host: str, port: int, timeout: float = 180.0) -> None:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2.0):
                return
        except OSError as exc:
            last = exc
            time.sleep(1.0)
    raise RconError(f"port {port} not open: {last}")
