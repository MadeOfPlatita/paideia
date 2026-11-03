# Restauración y verificación del modelo de capacidad

## Incidencia comprobada

El ledger de capacidad contenía URLs del Banco de España, Tesoro y CNMV asociadas a extractos de Cloudflare/Groq. El informe también había regenerado su bibliografía con esas URLs incorrectas. Esto se detectó leyendo el contenido, no solo por un fallo del verificador de IDs.

## Recuperación

- Se preservó una copia explícitamente marcada `INCIDENTE-ledger-corrupto-NO-USAR.json`.
- Se recuperaron de nuevo las ocho páginas oficiales de Cloudflare y Groq; las ocho respondieron HTTP 200.
- Se generó un ledger exclusivo en este directorio, con IDs 1–8 correspondientes a las fuentes que realmente respaldan el informe.
- Se adjuntaron extractos de cada respuesta guardada y se restauró `../source-ledger.json` desde el ledger generado, no reconstruyendo citas por intuición.
- Se regeneró la bibliografía de `../report.md`; `verify --strict --evidence` terminó en `citations OK`.

## Regresión del cálculo

La primera oleada de solicitudes con loops incluía resultados de herramientas aún no producidos. Se añadió primero una prueba: falló con `145000 != 111000`. Se sustituyó el máximo contexto de una llamada posterior por contexto estático + pregunta actual + salida inicial. Después pasaron seis tests y se regeneraron 432 escenarios y cuatro casos límite.

Los escenarios siguen siendo cálculos de cuotas bajo supuestos, no mediciones de latencia, calidad en español, herramientas o capacidad de cien inferencias simultáneas. La reparación de citas tampoco demuestra una integración con proveedores.
