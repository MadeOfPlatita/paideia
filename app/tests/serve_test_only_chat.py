"""Temporary loopback QA fixture: NEVER a real model or deployment entry point."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app
from backend_services import LocalChatService, CatalogueComparisonService
from pai_tools import ToolDispatcher
from structured_provider_adapter import FakeChatProvider, BrowserFixture
from test_functional05_http import make_gate


def main():
    parser = argparse.ArgumentParser(description="TEST ONLY: temporary loopback chat QA fixture")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--hold-slot", action="store_true", help="TEST ONLY: occupy a synthetic slot for queue UI checks")
    args = parser.parse_args()
    gate = make_gate()
    if args.hold_slot:
        gate.claim(gate.submit()["ticket"])
    repository = app.SnapshotRepository()
    service = LocalChatService(provider=FakeChatProvider(None, test_only=True, browser=BrowserFixture.SCENARIO), enabled=True, test_only=True,
        dispatcher=ToolDispatcher(repository, CatalogueComparisonService()), tools_enabled=True, admission=gate)
    server = app.create_server(port=args.port, repository=repository, chat_service=service)
    print("TEST ONLY: fake upstream, real local tool/HTTP path at http://127.0.0.1:" + str(server.server_port))
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
