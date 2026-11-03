
from pathlib import Path
from collections import Counter
import json, shutil
root=Path('C:/Users/aleja/Downloads/App Financiera')
base=root/'docs/qa-usuarios-20261103T165536'
source=root/'prototipos/paideia-local/docs/qa-usuarios-20261103T165536/exportacion'
dest=base/'exportacion'
if not dest.exists(): shutil.copytree(source,dest)
for f in ['exportacion/evidence.json','escenarios/evidence.json','biblioteca-navegacion/evidence.json','coordinador/reproduccion-home-formato.json']:
 json.loads((base/f).read_text(encoding='utf-8'))
issues=[
 {'id':'QA-01','title':'Guardado del informe no acreditado y sin orientación tras pulsar','priority':1,'severity':'alta','category':'funcional/UX','status':'flujo_bloqueado_reportado_y_verificacion_inconclusa','confirmed':'El informe se prepara, se observa beforeprint y el estado visible sigue igual; no es una descarga directa.','unknown':'Diálogo nativo, archivo guardado y causa del fallo del usuario en Hermes no verificados.','source':'exportacion/evidence.json','steps':['Calcular ambos escenarios','Pulsar Imprimir / guardar como PDF','Intentar terminar el guardado'],'recommendation':'Reproducir el flujo nativo y ofrecer una salida de archivo compatible; nunca afirmar guardado por beforeprint/afterprint o CDP PDF.'},
 {'id':'QA-02','title':'Inicio desborda horizontalmente en móvil','priority':2,'severity':'media','category':'visual/accesibilidad','status':'confirmado_reproducido_coordinador','confirmed':'Viewport de layout390px y contenido448px; spans de contexto ficticio llegan a448.17px.','source':'coordinador/reproduccion-home-formato.json','screenshot':'coordinador/home-contexto-desbordado.png','steps':['Abrir Inicio a390x844','Desplazarse a campos ficticios del chat'],'recommendation':'Permitir ajuste de cadenas largas en el contenedor concreto; probar sin rediseñar toda la web.'},
 {'id':'QA-03','title':'Resumen compara saldos de distintos horizontes sin mostrarlos','priority':3,'severity':'media','category':'contenido/UX','status':'confirmado_por_captura_y_codigo','confirmed':'La tabla tiene Escenario,Estado,Aportado,Saldo nominal,Saldo real, pero no horizonte ni aviso; los detalles sí muestran el plazo.','source':'escenarios/evidence.json','screenshot':'escenarios/screenshots/comparacion-horizontes.png','steps':['Calcular A a5años y B a10años','Leer el resumen comparativo sin bajar a los detalles'],'recommendation':'Añadir los plazos o una advertencia condicional al resumen, sin impedir comparar ni recomendar un ganador.'},
 {'id':'QA-04','title':'No se explica que filtro y selección se pierden al recargar','priority':4,'severity':'baja','category':'UX','status':'claridad_confirmada_no_requisito_de_persistencia','confirmed':'Filtrar depósito y seleccionar2; tras recargar vuelve todas/0. El texto indica que la selección no cambia sin pulsar, sin aclarar recarga.','source':'biblioteca-navegacion/evidence.json','steps':['Filtrar depósitos y seleccionar dos','Recargar la página'],'recommendation':'Aclarar que el estado es temporal; no añadir persistencia automática ni guardar datos por este hallazgo.'}
]
excluded=[{'id':'ESC-02','title':'Falta de separador de miles en importes de cuatro cifras','decision':'No confirmado como defecto; el coordinador reprodujo el comportamiento estándar de Intl.NumberFormat es-ES:2784,43€ frente a18.784,43€. Sería una decisión de formato, no prueba de incoherencia ni error financiero.'}]
unverified=['Descarga del adjunto de Hermes:reportada por el usuario, no reproducida por los testers; es un flujo distinto de window.print.', 'No consola completa fiable; no afirmar ausencia de errores.', 'Resultado comparativo con3y4candidatos,lectoresdepantalla,dispositivofísico,ycausahostdeimpresión no verificados.']
assert len({i['id'] for i in issues})==len(issues)
for issue in issues:
 assert (base/issue['source']).is_file()
 if 'screenshot' in issue: assert (base/issue['screenshot']).is_file()
result={'target':'http://127.0.0.1:8765/','testers':3,'code_changes':False,'user_session_modified':False,'demo_server_left_running':True,'findings':issues,'counts':{'total_prioritized_items':len(issues),'severity':dict(Counter(i['severity'] for i in issues)),'status':dict(Counter(i['status'] for i in issues))},'excluded_as_defects':excluded,'unverified':unverified,'export_evidence_note':'Original export artifacts preserved under prototipos/paideia-local/docs/...; copied here for one consolidated report.'}
print(json.dumps(result,ensure_ascii=False,indent=2))
