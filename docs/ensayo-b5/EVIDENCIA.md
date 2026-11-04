# B5 — ensayo ficticio con producto documentado

## Alcance y límites

El ensayo reutiliza los cinco pasos existentes: referencia del catálogo, condiciones, importe ficticio, comprensión y justificante. Las condiciones solo se presentan como documentadas cuando hay URL HTTPS y fecha de consulta; su estado se distingue y no se identifica como oferta vigente. No solicita credenciales, documentación ni datos personales; el importe es imaginado y el cierre indica que no se ha enviado ninguna solicitud ni movido dinero. EBN y Self Bank, que son extras curados, no se ofrecen como selección del ensayo existente: la revisión utilizó Openbank `DEP-02`. Sin verificación de impresión nativa ni móvil físico.

## Primera revisión independiente

Dictamen desfavorable: indicador de datos ausentes marcado como verificado, fuentes/fechas incompletas, falta de reintento, pérdida del importe y foco al terminar una carga, diferencias local/WSGI por los campos excluidos en el empaquetado y falta de referencia de fuente en el plazo. Se aplicó un ciclo de corrección sin publicar el cambio.

## Revisión independiente de la corrección

Dictamen informado: favorable. El revisor informó que realizó el recorrido de cinco pasos en navegador con Openbank y comprobó que solo se hicieron GET a estado, condiciones y catálogo; comprobó estado sin dato, URL y fecha, recuperación, importe y foco, correspondencia de candidatos entre el snapshot local y el empaquetado WSGI, y fuente del plazo. El dictamen se refiere a la versión local, no al despliegue público. No consta que haya comprobado impresión ni dispositivo físico. Transcripción técnica de revisión: `deleg_f8365df4` (sesión de Hermes).

## Regresión ejecutada por coordinación

- `python -B -m unittest discover -s tests -p 'test_*.py'`: terminó correctamente; esta ejecución de unittest no acredita casos exclusivos de otros recolectores.
- `node --check static/app.js` y `node --test tests/*.test.cjs tests/report_unit.js`: terminaron correctamente.
- El frontend fuente y el frontend empaquetado tenían SHA-256 `29426616614d8220cdd10cdc73b069d62edef827bc3e82ef5569905a06e70e37` tras la revisión.

La revisión observó que otras vistas no ofrecen reintento de condiciones; es un límite anterior fuera del alcance de este bloque. No se ha subido ni desplegado B5.
