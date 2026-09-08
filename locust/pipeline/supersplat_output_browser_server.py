#!/usr/bin/env python3
"""Restricted SuperSplat output browser.

Only exposes viewer assets and PLY files matching the 3DGS output layout.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


WORKSPACE = Path("/home/ecoplants/lyc/3Dgaussians")
OUTPUTS_ROOT = (WORKSPACE / "outputs").resolve()
VIEWER_ROOT = (WORKSPACE / "supersplat_viewer" / "public").resolve()
APP_ROOT = Path(__file__).resolve().parent
PLY_PATTERN = re.compile(r"^(.+)/point_cloud/iteration_(\d+)/point_cloud\.ply$")


def catalog() -> list[dict]:
    entries = []
    if not OUTPUTS_ROOT.is_dir():
        return entries
    for path in OUTPUTS_ROOT.glob("**/point_cloud/iteration_*/point_cloud.ply"):
        if not path.is_file():
            continue
        rel = path.relative_to(OUTPUTS_ROOT).as_posix()
        match = PLY_PATTERN.fullmatch(rel)
        if not match:
            continue
        stat = path.stat()
        entries.append({
            "id": rel,
            "experiment": match.group(1),
            "iteration": int(match.group(2)),
            "bytes": stat.st_size,
            "modified": int(stat.st_mtime),
        })
    entries.sort(key=lambda item: (item["experiment"].lower(), item["iteration"]))
    return entries


def resolve_ply(identifier: str) -> Path | None:
    identifier = unquote(identifier).replace("\\", "/").lstrip("/")
    if not PLY_PATTERN.fullmatch(identifier):
        return None
    candidate = (OUTPUTS_ROOT / identifier).resolve()
    try:
        candidate.relative_to(OUTPUTS_ROOT)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


class Handler(BaseHTTPRequestHandler):
    server_version = "SuperSplatOutputBrowser/1.0"

    def do_GET(self):
        request = urlparse(self.path)
        if request.path == "/api/catalog":
            self.send_json({"outputs": catalog()})
            return
        if request.path.startswith("/output/"):
            identifier = request.path[len("/output/"):]
            path = resolve_ply(identifier)
            if path is None:
                self.send_error(HTTPStatus.NOT_FOUND, "Unknown output PLY")
                return
            self.send_file(path, "application/octet-stream", allow_ranges=True)
            return
        if request.path in ("/", "/index.html"):
            self.send_file(APP_ROOT / "index.html", "text/html; charset=utf-8")
            return
        if request.path.startswith("/viewer/"):
            rel = unquote(request.path[len("/viewer/"):]) or "index.html"
            candidate = (VIEWER_ROOT / rel).resolve()
            try:
                candidate.relative_to(VIEWER_ROOT)
            except ValueError:
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            if not candidate.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            mime = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
            self.send_file(candidate, mime)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def send_json(self, value):
        payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def send_file(self, path: Path, content_type: str, allow_ranges: bool = False):
        size = path.stat().st_size
        start, end = 0, size - 1
        status = HTTPStatus.OK
        range_header = self.headers.get("Range") if allow_ranges else None
        if range_header:
            match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
            if not match:
                self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                return
            left, right = match.groups()
            if left:
                start = int(left)
                end = int(right) if right else end
            elif right:
                start = max(0, size - int(right))
            if start > end or start >= size:
                self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                self.send_header("Content-Range", f"bytes */{size}")
                self.end_headers()
                return
            end = min(end, size - 1)
            status = HTTPStatus.PARTIAL_CONTENT
        length = end - start + 1
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("X-Content-Type-Options", "nosniff")
        if allow_ranges:
            self.send_header("Accept-Ranges", "bytes")
        if status == HTTPStatus.PARTIAL_CONTENT:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        try:
            with path.open("rb") as handle:
                handle.seek(start)
                remaining = length
                while remaining:
                    chunk = handle.read(min(1024 * 1024, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    if args.host != "127.0.0.1":
        parser.error("Only --host 127.0.0.1 is permitted")
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Listening on http://{args.host}:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
