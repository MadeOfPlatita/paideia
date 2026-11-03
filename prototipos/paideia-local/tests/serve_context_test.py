"""Loopback-only synthetic context QA; no external provider or secrets."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
from backend_services import LocalChatService
from structured_provider_adapter import FakeChatProvider, BrowserFixture

if __name__ == '__main__':
    service = LocalChatService(provider=FakeChatProvider(None, test_only=True, browser=BrowserFixture.CONTEXT), enabled=True, test_only=True, context_enabled=True, history_enabled=True)
    server = app.create_server(port=0, chat_service=service)
    print('TEST ONLY loopback port:', server.server_port, flush=True)
    try: server.serve_forever()
    finally: server.server_close()
