"""One final small local review; model output is data, not code."""
from datetime import datetime
from pathlib import Path
import json
import urllib.request

out = Path(__file__).resolve().parent
cutoff = datetime.fromisoformat('2026-11-03T14:38:42+01:00')
now = datetime.now().astimezone()
assert now < cutoff, 'Mission expired'
source = out.parents[1] / 'prototipos/paideia-local/static/context_help.js'
assert source.is_file()
code = source.read_text(encoding='utf-8')
prompt = ('Revisa SOLO este archivo de ayuda educativa local para un usuario. '
          'No puedes ejecutar pruebas ni buscar otros archivos. '
          'Pregunta concreta: ¿hay un error demostrable en abrir/cerrar/Escape/foco o una simplificación '
          'que conserve exactamente accesibilidad, validación y API? '
          'Responde en español en menos de150palabras. Si no hay caso concreto, di que no propones cambios. '
          'No afirmes que algo es código muerto sin comprobar todos sus usuarios. '
          'No reescribas el archivo. /no_think\n\n' + code)
payload = {'model': 'qwen3.6-35b-a3b', 'messages': [{'role': 'user', 'content': prompt}],
           'temperature': 0, 'max_tokens': 2500}
status = {'started': now.isoformat(), 'model': payload['model'],
          'scope': 'static/context_help.js only', 'type': 'unverified static suggestion',
          'previous_attempt': 'QWEN-AUDIT-RAW.json; length with empty content'}
(out / 'QWEN-RETRY-STATUS.json').write_text(json.dumps(status, indent=2), encoding='utf-8')
try:
    request = urllib.request.Request('http://127.0.0.1:1234/v1/chat/completions',
        data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=420) as response:
        result = json.load(response)
    choice = result['choices'][0]
    status.update(content=choice['message'].get('content', ''), finish_reason=choice.get('finish_reason'),
                  usage=result.get('usage'), response_model=result.get('model'))
    status['usable_content'] = bool(status['content'].strip()) and status['finish_reason'] == 'stop'
except Exception as exc:
    status.update(error=type(exc).__name__ + ': ' + str(exc), usable_content=False)
finally:
    status['completed'] = datetime.now().astimezone().isoformat()
    (out / 'QWEN-RETRY-RESULT.json').write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(status, ensure_ascii=False))
