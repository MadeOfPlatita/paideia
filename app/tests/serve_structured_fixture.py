"""Loopback-only structured education fixture; never a real provider."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
from backend_services import LocalChatService
from structured_provider_adapter import FakeChatProvider, StructuredProviderAdapter

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8771)
    args=parser.parse_args()
    provider=StructuredProviderAdapter(FakeChatProvider(None, test_only=True, scripted=True), test_only=True)
    service=LocalChatService(provider=provider,enabled=True,test_only=True,structured_mode=True)
    server=app.create_server(port=args.port, chat_service=service)
    print('STRUCTURED_FIXTURE test_only=True port='+str(server.server_port),flush=True)
    try: server.serve_forever()
    finally: server.server_close()

if __name__=='__main__':
    main()
