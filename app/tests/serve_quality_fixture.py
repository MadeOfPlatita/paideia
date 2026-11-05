"""TEST ONLY: local UI regression, no model, credentials or remote transport."""
from pathlib import Path
import sys, threading
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
from backend_services import LocalChatService
from structured_provider_adapter import FakeChatProvider, BrowserFixture
if __name__=='__main__':
    server=app.create_server(port=8769,chat_service=LocalChatService(provider=FakeChatProvider(None, test_only=True, browser=BrowserFixture.QUALITY),enabled=True,test_only=True))
    threading.Timer(180,server.shutdown).start()
    print('QUALITY_FIXTURE test_only=True url=http://127.0.0.1:8769/',flush=True)
    try: server.serve_forever()
    finally: server.server_close()
