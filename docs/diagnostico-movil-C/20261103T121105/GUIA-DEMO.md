# Demo actual — escenarios, informe y biblioteca

## Estado
A (escenarios), B (informe) y C (biblioteca, diagnóstico y ayudas) tienen revisión independiente favorable en los alcances documentados. C se aceptó tras diagnosticar el arnés, sin modificar producción. No significa producto final, catálogo contractual aprobado ni IA real validada.

## Arrancar
En la carpeta `C:/Users/aleja/Downloads/App Financiera/prototipos/paideia-local`, ejecutar:

```text
python3 -B app.py --port 8765
```

Si el intérprete de vuestra terminal se llama `python`, usar `python -B app.py --port 8765`. Abrir http://127.0.0.1:8765/#escenarios . Mantener la terminal y el ordenador encendidos. Si el puerto está ocupado, no detener procesos ajenos. No introducir datos reales ni claves; no hace falta guardar un perfil.

## 1. Escenarios e informe
En ambos escenarios: capital inicial 1000 €, tasa anual hipotética 3 %, plazo 5 años, aportación mensual 50 € e inflación 2 %. A compuesto, B simple. Calcular cada uno.

Explicar: «Son hipótesis manuales, no ofertas. El motor calcula los resultados; no la IA. Las aportaciones se hacen al final del mes y se excluyen impuestos y costes».

Mirar resumen, gráficos y tablas. Cambiar la tasa de A sin recalcular: sus resultados dejan de estar vigentes y B permanece. Recalcular. Con ambos actuales, pulsar **Imprimir / guardar como PDF**. Es la impresión del navegador, no una descarga automática. No se ha probado impresora física ni el guardado manual del diálogo.

PDF real ya disponible: `../../noche-funcional/20261103T003723/B/DEMO-1000-3-5.pdf`. Su referencia numérica y guion original se conservan en `../../noche-funcional/20261103T003723/GUIA-DEMO.md`.

## 2. Biblioteca y comparación sin inventar rentabilidad
1. Ir a Biblioteca y filtrar la familia de depósitos.
2. Abrir una ficha y señalar fuente y estado. Identidad verificada no equivale a condiciones actuales aprobadas.
3. Añadir dos depósitos a comparar. Comparar metadatos y pulsar Diagnosticar.
4. Leer los motivos por los que no se ofrece una comparación cuantitativa. No afirmar cuál rinde más ni presentar un ranking.
5. Abrir una ayuda TAE/TIN/liquidez/riesgo. Las definiciones también están en el glosario; inflación e interés compuesto aparecen en escenarios. Son explicaciones educativas, no asesoramiento.

No hace falta inyectar textos excedidos ni retener respuestas para una demo normal: esas regresiones están cubiertas por la evidencia técnica.

## Límites y cierre
El móvil se verificó por emulación, no en dispositivo físico ni mediante auditoría visual de todas las pantallas. El catálogo no son ofertas cuantitativas publicables. Pai no está conectado por esta entrega; calidad real, contexto e infraestructura siguen pendientes.

Al terminar, detener únicamente el servidor de esta demo con Ctrl+C. Las comparaciones de escenarios no se conservan al recargar. Esta aplicación local no es un enlace público para clase.

Resultado y dictamen actual: `RESULTADOS.md` e `independiente/REVISION-COMPLETA.json`.
