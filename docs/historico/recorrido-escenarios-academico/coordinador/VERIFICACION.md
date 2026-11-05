# Prueba del coordinador — recorrido académico

Navegador aislado `journey-coordinator`, API local8765; no se tocó el preview del usuario. Datos ficticios.

## Recorrido observado
Cargar ejemplo en A vacío → copiar A a B vacío → cambiar solo tasa de B de2%a3% → calcular A y B → leer diferencias → guía Guardar → descargar HTML. Cargar/copiar no emitieron fetch; los dos cálculos explícitos emitieron exactamente dos POST /api/calculate. Ambos resultados quedaron actuales y el resumen explicó solo el cambio de tasa, con horizonte5años común. Detalles en `recorrido.json`.

Archivo de esta descarga:`informe-comparacion.html`,4739bytes,SHA2566c8228b63c79a4d68dd3cac0b61d608b0cc00da63f5ca79202a118cbfbb62f98. Lectura desde disco:5tablas, sin scripts ni referencias externas de recursos; saldos finales,reales y aportaciones coinciden con las respuestas del motor guardadas en recorrido.json. No se ha generado con write_file ni Page.printToPDF. Es descarga de navegador aislado, **no repetición del diálogo nativo de Hermes** probado en el cierre anterior.

Primer Browser.setDownloadBehavior exitoso no produjo archivo: se conservó el fallo de aserción de existencia. Se configuró Page.setDownloadBehavior en el target y se repitió una vez el clic real; el archivo se escribió y se leyó después. La primera observación tras existir daba4046bytes y la lectura posterior4739: no tomar la mera existencia/tamaño preliminar como finalización de una descarga. No se atribuye esta configuración de automatización a un defecto de la web.

## Hallazgo de teclado pendiente de revisión independiente
Con foco en enlace Guardar, Enter real por CDP desplaza el informe a top15,64px pero el foco permanece en ese enlace. Tab real posterior enfoca #scenario-principal y devuelve el informe a top4627,64px. El usuario de teclado vuelve a A en lugar de continuar con el guardado. Hash sigue #escenarios, de modo que no es pérdida de ruta sino de continuidad del foco. Evidencia:`teclado-guia.json`,`teclado-guia-tab.json`.

Se ha trasladado el caso al revisor independiente deleg_ef545abe / sa-0-eb71c3a8, sin cambiar las fuentes durante su ejecución. No declarar todavía el recorrido aprobado. No se hizo auditoría completa de accesibilidad ni se activó IA.

## Resultado del dictamen y corrección de ciclo 1

El revisor independiente **no aprobó** el recorrido: un defecto de severidad media, reproducido, en la guía «Guardar». Con ambos escenarios calculados, Enter sobre el enlace desplazaba la página al informe pero dejaba el foco en el enlace; el Tab siguiente volvía a Capital inicial de A. Dictamen y evidencia en `revision/REVISION-INDEPENDIENTE.json` y `revision/teclado.json`; no se borran. Los probes propios del revisor sí pasaron en 1280 y 390 px (confirmación/cancelación A/B, revalidación, respuestas tardías, seis diferencias, tasas de cuatro decimales) y la descarga HTML real se leyó desde disco con cinco tablas.

Corrección acotada `deleg_9d13a2da` en el handler común: el destino recibe `tabindex=-1`, foco con `preventScroll` y el desplazamiento que ya existía. RED antes del parche en los tres destinos, GREEN después; 24 combinaciones de Enter/Tab reales en ambos tamaños; recorrido, informe, descarga y layout pasaron. Detalle en `correccion-foco-1/CORRECCION.md`.

El coordinador reprodujo el caso de forma independiente con teclado real por CDP, en documentos nuevos y sesión aislada (`foco-ciclo1.json`): a 1280 px, Enter deja el foco en `scenario-report-host`, el hash sigue en `#escenarios` y Tab llega a «Imprimir / guardar como PDF»; a 390 px con guard de impresión, Tab llega a «Descargar informe (HTML)» con el aviso de impresión desactivada, sin desbordamiento (390/390). También quedó escrito el guion de demo en `GUION-DEMO.md`.

**Gate independiente superado.** El reintento `deleg_f39b6115` devolvió dictamen **favorable** (`passed: true`, sin problemas de seguridad ni errores lógicos): 9/9 comprobaciones de foco y 33/33 del recorrido en 1280 y 390 px, con Enter/Tab reales, hash `#escenarios`, snapshot sin cambios y cero solicitudes nuevas; evidencia en `revision-foco-1/` (JSON, capturas). Sus `verification_blockers` recogen los límites ya excluidos en el plan (impresión/PDF nativo, auditoría global) y que no re-ejecutó los estados pending/error, cubiertos por `GREEN-teclado.json` del ciclo de corrección; no son defectos nuevos. Fuentes sin cambios desde el parche (18:25). El hito se declara aceptado en este alcance; no se probó impresión nativa ni PDF, ni auditoría global de accesibilidad o seguridad.
