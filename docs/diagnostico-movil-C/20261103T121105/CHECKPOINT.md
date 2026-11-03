# Checkpoint — integración independiente completada, matriz suplementaria pendiente

## Verificado por el coordinador
Se leyeron y analizaron programáticamente `independiente/desktop.json` y `mobile.json`: ambos tienen result.ok=true y27/27comprobaciones correctas. Viewports finales1440/1440 y390/390. `independiente/probes.json` conserva9/9casos de consultas y un reintento de teclado real correcto; el primer intento de teclado fallido se conserva, no se oculta.

Los cinco SHA256 de `SOURCE-HASHES.json` coinciden con app.py,app.js,context_help.js/css y c_integration_browser.js actuales. No se modificaron fuentes ni assertions/tiempos de la prueba.

## Por qué no se ha aprobado aún
El revisor devolvió passed:false únicamente porque no completó navegación fuera/vuelta para cada variante inválida ni cambio de filtro mientras se mantiene el texto inválido. Es evidencia faltante, no fallo nuevo ni un tercer ciclo de corrección. No debe convertirse en aprobado mediante los pases parciales.

Suplemento independiente despachado deleg_dacd6f5d. Solo prueba esa matriz sobre4textos:101letras,100letras+espacio,espacio+100letras y101espacios; navegación, filtro alternativo, navegación de nuevo, restauración de filtro sin fetch y borrado final válido. Dictamen combinado en `independiente/REVISION-COMPLETA.json`; conservar el dictamen anterior.

## Límite y runtime
No se abre segundo experimento diagnóstico por rutina: el primero demostró el límite de evaluación y el lanzamiento separado resuelve la ejecución del test intacto. No se repiten suites sin cambios ni auditoría amplia Qwen. El servidor18874delcoordinador está cerrado; suplemento usa propio18876ydebe cerrarlo. No hay aceptación hasta leer la matriz y el dictamen completos.
