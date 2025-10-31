"""간단한 정적 웹 서버.

이 스크립트는 저장소 루트 디렉터리에서 `index.html`을 기본 문서로 제공하는
경량 웹 서버를 구동합니다. Python 표준 라이브러리만 사용하므로 별도 설치가
필요하지 않습니다.
"""
from __future__ import annotations

import argparse
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent


class QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
    """로깅 출력 형식을 다듬은 핸들러."""

    def log_message(self, format: str, *args) -> None:  # noqa: A003 - http.server 시그니처 준수
        client_ip = self.client_address[0]
        message = format % args
        self.server.logger(f"[{client_ip}] {message}")  # type: ignore[attr-defined]


class StaticServer(ThreadingHTTPServer):
    """index.html을 제공하는 ThreadingHTTPServer."""

    def __init__(self, server_address: Tuple[str, int], *, directory: Path, logger) -> None:
        handler = partial(QuietHTTPRequestHandler, directory=str(directory))
        super().__init__(server_address, handler)
        self.logger = logger


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="정적 자산을 제공하는 개발용 웹 서버")
    parser.add_argument("--host", default="127.0.0.1", help="서버 바인딩 주소 (기본값: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="서버 포트 (기본값: 8000)")
    return parser.parse_args(argv)


def run_server(host: str, port: int) -> None:
    os.chdir(REPO_ROOT)

    def logger(message: str) -> None:
        print(f"[server] {message}")

    with StaticServer((host, port), directory=REPO_ROOT, logger=logger) as httpd:
        logger(f"http://{host}:{port} 에서 index.html 제공 중")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger("서버를 종료합니다.")


def main(argv: Optional[list[str]] = None) -> None:
    args = parse_args(argv)
    run_server(args.host, args.port)


if __name__ == "__main__":
    main()
