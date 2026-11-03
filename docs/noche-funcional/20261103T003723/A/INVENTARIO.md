# Descubrimiento A

- `domain.calculate_scenario` y `/api/calculate` ya calculan una serie y resumen deterministas; las cifras son cadenas decimales EUR, con aportaciones al final del mes, tasas y convenciones diferenciadas, sin costes ni impuestos.
- `#escenarios` ya contiene formulario, validación básica, resumen, SVG nominal/real/aportado y tabla accesible anual, además de avisos de pérdidas; invalida al editar pero desactiva el formulario mientras espera.
- Solo hay un escenario: comprobación de navegador RED en `red-browser.json` y captura. `#comparar` corresponde a metadatos de productos, no compara hipótesis. El gráfico y la tabla existentes se reutilizarán sin fórmulas financieras alternativas.
- Delta: dos formularios/resultados independientes en la misma ruta, invalidación por versión incluso durante peticiones, contrato de snapshot para informe, errores aislados y verificación de navegador con motor local. No se requiere perfil ni IA; no se modifica backend.
