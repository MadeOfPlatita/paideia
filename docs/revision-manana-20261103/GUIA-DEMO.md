# Demo lista: escenarios e informe, sin IA

## Qué mostrar
A y B tienen revisión independiente favorable previa y regresión nueva de esta mañana. Biblioteca/ayudas C se conservan, pero su aceptación móvil independiente está bloqueada: no presentarlas como entrega aprobada. No hay IA real conectada ni catálogo cuantitativo publicable.

## Arranque
1. En una terminal abre la carpeta `C:/Users/aleja/Downloads/App Financiera/prototipos/paideia-local`.
2. Ejecuta `python3 -B app.py --port 8765` (si en tu terminal el intérprete instalado se llama `python`, usa `python -B app.py --port 8765`). Si el puerto está ocupado no mates procesos ajenos.
3. Abre http://127.0.0.1:8765/#escenarios . El ordenador y esa terminal deben permanecer activos. Es una app local, no un enlace público.
4. No introduzcas claves ni datos reales. No hace falta guardar un perfil.

## Tres minutos para José Manuel
- En ambos escenarios:capital1000€,tasa3%,plazo5años,aportaciónmensual50€,inflación2%. Acompuesto;Bsimple. Pulsar CalcularA yCalcularB.
- Explicar:son dos hipótesis manuales, no ofertas. Las aportaciones son al final de mes; nominal y poder adquisitivo no son lo mismo; costes e impuestos excluidos.
- Ver tabla comparativa ygráficos. La demo verificada previamente da saldonominalA4388,32€ yB4371,25€; la referencia con detalles está en `../noche-funcional/20261103T003723/GUIA-DEMO.md`.
- Cambiar latasaA sincalcular:sus resultados dejan de estar vigentes, B permanece. RecalcularA. No se promete persistencia tras recargar.
- Con ambos actuales,pulsar **Imprimir / guardar como PDF**. El navegador abre su impresión; elegir Guardar comoPDF si se desea. No es descarga automática. El diálogo manual y la impresora física no se han probado.
- Mostrar el PDF ya generado si no hay tiempo para el diálogo:`../noche-funcional/20261103T003723/B/DEMO-1000-3-5.pdf`.

## Si preguntan por Pai o productos
«El motor de la aplicación hace estos cálculos, no laIA. Pai conserva arquitectura y pruebas sintéticas; integración real ycalidad siguen pendientes. Los candidatos de biblioteca no son ofertas vigentes aprobadas».

## Cierre y límites
Cerrar únicamente la terminal del servidor de esta demo conCtrl+C. No habilitar proveedor,publicar ointroducir claves para esta explicación. Resultado y pendientes:`RESULTADOS.md`. No hacer tercer ciclo deC sin nueva decisión del equipo.
