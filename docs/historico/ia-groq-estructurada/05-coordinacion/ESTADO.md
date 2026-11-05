# Estado de integración Groq estructurada — 30 de octubre de 2026

## Resultado

Trabajo exclusivamente offline. Se construye un payload Groq `json_schema` con `strict:false`, se entrega a transportes ficticios y se valida la selección cerrada para renderizado y cálculo local. No se ha conectado a Groq ni a la sesión segura real. El proveedor contado sintético solo admite su fake exacto; su contador no es el ledger real, y el constructor de sesión real está deliberadamente deshabilitado.

## Verificación

- Coordinación: `python -B -m unittest discover -s tests -p 'test_*.py' -q`: **316 pruebas OK** tras la corrección.
- Regresión anterior a la corrección: 315 Python, 33 Node y 19 HTTP; evidencia `regresion-contado-offline.json`. No se afirma nueva ejecución Node/HTTP tras el cambio, limitado a proveedor y test Python.
- Revisión independiente del puente offline `deleg_83603e56`: aprobada para ese alcance.
- Revisión independiente inicial del proveedor sintético `deleg_8bf65bff`: no aprobada por datos en variables locales en el traceback. Revisión posterior `deleg_74d8ce65`: aprobada en el alcance sintético; seis casos adversariales y cuatro pruebas existentes. La captura de locales en frames del llamador aún puede revelar datos; no hay garantía general de privacidad.
- No hubo petición real a Groq, credenciales, activación de sesión, instalaciones ni despliegue durante esta ejecución.

## Pendientes y límites

La integración de extremo a extremo HTTP → admisión → misión/ledger → transporte real → salida estructurada no se ha implementado ni revisado. Es necesario enlazarla sin debilitar la autorización, el consentimiento, el control tras la conexión, la revocación, el singleflight y la cuota, y probarla con transporte simulado antes de cualquier ensayo externo. Un intento de implementación se detuvo al no verificar esas garantías; no constituye prueba de imposibilidad. No reutilizar misiones caducadas. Una prueba real futura requiere autorización específica, nueva misión válida, confirmación humana del plan Free e introducción voluntaria de la clave mediante la ventana segura.

Los mensajes de sistema del constructor pueden ser arbitrarios: no se ha probado una política de procedencia para una sesión real. El fake almacena sus solicitudes para inspección. Un 429 ficticio se presenta como `invalid_response` sin reintento. `sent_state=unknown` tras entrar en `post` es conservador y no acredita que se hayan enviado bytes. No capturar variables locales en producción.

La documentación de Groq consultada lista el modelo `openai/gpt-oss-20b` con `strict:false`, pero incluye un ejemplo contradictorio con `strict:true`. La compatibilidad efectiva con el proveedor y la calidad del modelo siguen sin verificar. Tests ficticios y HTTP local no son prueba real.
