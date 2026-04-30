#!/usr/bin/env python3
import json
import os
import socket
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HOST = os.getenv("SPEEDTEST_HOST", "0.0.0.0")
PORT = int(os.getenv("SPEEDTEST_PORT", "8765"))
STATIC_DIR = Path(__file__).parent / "static"
RANDOM_CHUNK = os.urandom(1024 * 1024)


def json_bytes(payload):
    return json.dumps(payload).encode("utf-8")


def best_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


class SpeedTestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_OPTIONS(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Max-Age", "600")
            self.end_headers()
            return
        self.send_error(404, "Not Found")

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/ping":
            self.handle_ping()
            return
        if parsed.path == "/api/download":
            self.handle_download(parsed.query)
            return
        if parsed.path == "/api/server-info":
            self.handle_server_info()
            return
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/upload":
            self.handle_upload()
            return
        self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        return

    def send_api_headers(self, content_type, content_length=None):
        self.send_header("Content-Type", content_type)
        if content_length is not None:
            self.send_header("Content-Length", str(content_length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")

    def handle_ping(self):
        payload = {
            "server_time_ms": int(time.time() * 1000),
            "server_perf_ns": time.perf_counter_ns(),
        }
        body = json_bytes(payload)
        self.send_response(200)
        self.send_api_headers("application/json", len(body))
        self.end_headers()
        self.wfile.write(body)

    def handle_server_info(self):
        payload = {
            "host": socket.gethostname(),
            "bind": f"{HOST}:{PORT}",
            "local_ip": best_local_ip(),
            "note": "Run this server on a remote host/VPS for real internet speed measurement.",
        }
        body = json_bytes(payload)
        self.send_response(200)
        self.send_api_headers("application/json", len(body))
        self.end_headers()
        self.wfile.write(body)

    def handle_download(self, query_string):
        params = parse_qs(query_string)
        size = int(params.get("size", ["4000000"])[0])
        size = max(1, min(size, 50_000_000))
        self.send_response(200)
        self.send_api_headers("application/octet-stream", size)
        self.end_headers()
        remaining = size
        while remaining > 0:
            chunk = RANDOM_CHUNK[: min(len(RANDOM_CHUNK), remaining)]
            self.wfile.write(chunk)
            remaining -= len(chunk)

    def handle_upload(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        start = time.perf_counter()
        read = 0
        while read < content_length:
            data = self.rfile.read(min(1024 * 1024, content_length - read))
            if not data:
                break
            read += len(data)
        elapsed_ms = (time.perf_counter() - start) * 1000
        body = json_bytes({"received_bytes": read, "ingest_ms": elapsed_ms})
        self.send_response(200)
        self.send_api_headers("application/json", len(body))
        self.end_headers()
        self.wfile.write(body)


def main():
    STATIC_DIR.mkdir(exist_ok=True, parents=True)
    server = ThreadingHTTPServer((HOST, PORT), SpeedTestHandler)
    local_ip = best_local_ip()
    print(f"Speed test server bind: {HOST}:{PORT}")
    print(f"Open locally: http://127.0.0.1:{PORT}")
    print(f"LAN URL: http://{local_ip}:{PORT}")
    print("Deploy on public host for true WAN speed tests.")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
