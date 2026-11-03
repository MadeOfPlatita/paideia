"""Independent send-race probe. Mock HTTPS only; no network or real credentials."""
from pathlib import Path
import sys,json,threading
from unittest.mock import patch
APP=Path(__file__).resolve().parents[4]/'prototipos/paideia-local'
sys.path[:0]=[str(APP),str(APP/'tests')]
import providers
from secure_groq_session import Session
from test_secure_groq_session import Clock
entered,release=threading.Event(),threading.Event()
emissions=[]
class Reply:
    status=200
    def read(self,n):
        return b'{"choices":[{"message":{"role":"assistant","content":"SYNTHETIC PROBE"},"finish_reason":"stop"}]}'
class FakeConnection:
    connected=False
    def __init__(self,*args,**kwargs): pass
    def connect(self):
        entered.set()
        if not release.wait(5): raise TimeoutError()
        self.connected=True
    def request(self,*args,**kwargs):
        if not self.connected:self.connect()
        emissions.append(session.status()['state'])
    def getresponse(self):return Reply()
    def close(self):pass
class TestOnlyHTTPTransport(providers.GroqHTTPSJSONTransport):
    test_only=True
session=Session('SYNTHETIC_BOUNDARY_NOT_A_REAL_KEY',transport=TestOnlyHTTPTransport(),clock=Clock(),test_only=True)
outcomes=[]
def invoke():
    try:
        session.provider.chat([{'role':'user','content':'Synthetic boundary probe'}])
        outcomes.append('returned')
    except providers.ProviderError as error:outcomes.append(error.code)
with patch.object(providers.http.client,'HTTPSConnection',FakeConnection):
    thread=threading.Thread(target=invoke,daemon=True);thread.start()
    assert entered.wait(3),'Probe did not reach connection boundary'
    session.revoke();release.set();thread.join(8)
report={'test_only':True,'real_network_calls':0,'simulated_emission_states':emissions,'outcomes':outcomes,'thread_finished':not thread.is_alive(),'passed':not emissions and not thread.is_alive()}
print(json.dumps(report))
raise SystemExit(0 if report['passed'] else 1)
