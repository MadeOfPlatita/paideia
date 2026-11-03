# Fondos tradicionales — recuperación directa del coordinador

**Estado:** investigación recuperada con fuentes primarias y una descarga real. No existe integración en PostgreSQL ni autorización nueva de publicación. La entrega delegada de este frente falló; no se cuenta como informe válido del subagente.

## Conclusión

Sí hay datos importables de fondos tradicionales concretos. Se comprobó una descarga pública de Bestinver Bolsa, F.I., enlazada desde su página oficial: devuelve un XLSX real de valores liquidativos. Es una vía acotada por gestora/producto, no una API universal de fondos comercializados en España.[12][14]

## Candidatos y cobertura por campo

| Fuente | Identidad | Valor liquidativo / historial | Costes y documentos | Acceso / limitación |
|---|---|---|---|---|
| Bestinver, producto Bolsa | Página: ISIN ES0147622031; el XLSX solo identifica el nombre. Conservar el vínculo página→productId=2→archivo; no unir por nombre solamente. | XLSX descargado: 10.554 filas, 10.554 fechas distintas, 01-12-1997 a 23-10-2026; último valor 140,296021 EUR. | La página publica comisiones de gestión/depósito y mínimos; no tratar su suma como coste total KID ni suponer que recoge todas las condiciones. | GET público 200; descarga web, sin contrato de API/cuota/SLA verificado. Derechos de automatización, retención y display pendientes.[12][14] |
| CNMV, ejemplo OLEA NEUTRAL, FI | ISIN ES0118537002, registro, gestora y depositaria. | No hay NAV en la ficha inspeccionada. | Fechas/enlaces de folleto y DFI; no tabla de costes completa. | HTML de consulta probado. Datos maestros, no feed diario de valor liquidativo ni licencia abierta deducible del acceso.[9] |
| VDOS | El proveedor declara cobertura amplia de fondos nacionales e internacionales registrados en España. | Cobertura comercial documentada, no descarga o API probada. | Documentación y campos financieros según descripción del servicio. | No se corroboró acceso API gratuito, endpoint, precio o licencia académica. Solicitud comercial/educativa pendiente; no se contactó.[11] |
| FundFacts | API por ISIN documentada; demo probada de un ETF, no de un fondo tradicional. | La demo no acredita cobertura de NAV diario de fondos españoles. | Devuelve costes y otras métricas en esa única demo. | Documentación de cuotas contradictoria y uso gratuito descrito como personal. No usar como solución de aula ya aprobada.[6][7][8][15] |

## Prueba Bestinver reproducible y límites

Petición real: `GET https://www.bestinver.es/WS/Api/Profitability/DownloadExcelLiquidity?productId=2`.[12]

Se recibió HTTP 200 y `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`. El archivo tiene 192.506 bytes; la integridad ZIP pasó y se analizó la hoja `Historico_Valores_Liquidativos`, con título y dos columnas. No se ejecutó código del fichero ni se instaló una biblioteca para leerlo.[12]

- Los valores son texto decimal con coma; normalizar con Decimal, no con un reemplazo ambiguo de separadores de miles.
- El historial tiene fechas de calendario: no afirmar que sean exclusivamente sesiones bursátiles.
- La página y la hoja coinciden en producto y fecha final; la página redondea el NAV. Eso no valida independientemente todos los valores del historial.[12][14]
- El ISIN de la página pasó formato y checksum. El archivo no contiene el ISIN; el enlace de descarga es la evidencia del mapping, no un match difuso por nombre.[12][14]
- No se han verificado distribución, ajustes históricos, cambios de política, continuidad de la URL ni licencia de reproducción. No publicar el histórico completo ni prometer actualización diaria automática todavía.

Evidencia local: `evidencia-coordinador/bestinver-nav-download.bin` (XLSX), `bestinver-nav-headers.txt`, `bestinver-nav-inspeccion.json`, `12.txt` y `10-bestinver-webextract.txt`. El JSON guarda SHA-256, fecha UTC real, filas y extremos; no se inventó una respuesta JSON de proveedor.

El GET inicial mediante urllib falló por certificado del cliente. Se recuperó mediante extracción web y curl con validación TLS activada; no se usó `--insecure`, credenciales ni evasión de controles.

## Contradicción FundFacts que afecta a la selección

La página de precios recuperada dice Free **5 lookups/mes** y Pro **1.000 requests/mes a 49 USD/mes**; el documento de requests dice Free **15** y Pro **9.000**. Ambas son fuentes oficiales recuperadas: no atribuir una cuota efectiva a una cuenta no creada ni elegir la más favorable.[6][15]

La página comercial limita Free/Starter a evaluación/uso personal, mientras los términos generales permiten uso en aplicaciones incluso comerciales sin resolver expresamente el plan. La demo pública no despeja el permiso para una web de clase. Pedir aclaración antes de integrar; no activar pruebas con tarjeta ni pago.[6][7][8]

## Propuesta para Paideia

Preparar catálogo de clases concretas, con identidad verificada; importar series mediante adaptadores pequeños por emisor solo cuando se aclaren los usos permitidos. Mantener por separado clase, distribuidor, comisiones documentadas, NAV e hipótesis del simulador. El histórico de un fondo de renta variable no es una rentabilidad prometida ni una tasa contractual de depósito.

## Sources

[6] https://fundfactsapi.com/pricing
[7] https://fundfactsapi.com/terms
[8] https://fundfactsapi.com/api/v1/demo/funds/IE00B4L5Y983
[9] https://www.cnmv.es/portal/consultas/iic/fondo?lang=es&nif=V85962447
[11] https://www.vdos.com/es/datos.html
[12] https://www.bestinver.es/WS/Api/Profitability/DownloadExcelLiquidity?productId=2
[14] https://www.bestinver.es/fondos-de-inversion/bestinver-bolsa
[15] https://fundfactsapi.com/docs/requests
