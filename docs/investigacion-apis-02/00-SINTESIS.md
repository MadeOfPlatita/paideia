# Segunda ronda de datos — síntesis contrastada

## Resultado y lectura recomendada

Los diez frentes tienen informe y JSON estructurado. El frente 02 se recuperó directamente tras fallar el agente; no se cuenta el fallo como investigación completada. El agregado contiene **177 registros de fuentes y 169 URLs distintas**, con procedencia por informe; son observaciones, no 177 afirmaciones corroboradas de forma independiente. Véanse `00-VALIDACION.json` y `00-FUENTES-AGREGADAS.json`.

**Conclusión:** sí hay datos reales importables para un catálogo propio, pero no se ha acreditado una fuente gratuita que cubra todas las condiciones y derechos de las cinco familias. PostgreSQL ayuda a normalizarlos; no resuelve por sí solo su calidad ni sus permisos.

## Hallazgos decisivos comprobados por el coordinador

### 1. Fondos tradicionales: descarga utilizable, no ausencia de datos

Bestinver Bolsa dispone de una descarga pública de histórico NAV. El XLSX real inspeccionado tiene 10.554 registros y fechas del 01-12-1997 al 23-10-2026; la página oficial aporta el ISIN ES0147622031. Es un resultado para una gestora/producto concreto, no una API universal ni una licencia de redistribución.[12][14]

El informe recuperado `02-fondos-tradicionales.md` conserva método, comprobación de identidad, archivo, hash y límites. No se creó una tabla de producción ni se publicó ese historial.

### 2. YieldMeister: útil para descubrir, insuficiente para comparar automáticamente

La página de precios publica 1.000 llamadas/mes en Free. Los términos permiten uso dentro de aplicaciones propias, requieren atribución visible y restringen la redistribución del dataset independiente; no queda corroborado un permiso irrestricto de caché histórica/exportación.[2][3]

La respuesta pública conservada contiene **70 registros globales**, pero solo **4 con market=ES**: dos benchmarks, una letra y un depósito. No son 70 productos españoles ni cuatro ofertas bancarias.[4]

**Conflicto concreto:** la fila de Openbank indica `term_months=12` y “Depósito Plazo Fijo 12m”, con tasa 3,25. Su propia URL oficial conduce a un depósito de **6 meses**; además, la página distingue una remuneración con ingreso mensual y otra sin él. El feed no recoge esas condiciones completas.[4][13]

Resultado: conservar como candidato secundario de descubrimiento/contraste. La fila conflictiva queda fuera de comparación hasta resolver identidad y condiciones; `stale=false` del proveedor no certifica exactitud. No cambiar silenciosamente 12 por 6 ni asumir que `rate` significa TAE.[4][13]

### 3. FundFacts: demo real, cuotas y permiso sin cerrar

La demo pública devuelve datos estructurados de un ETF por ISIN, con costes, riesgo y fechas. Eso prueba forma de respuesta para esa clase, no cobertura general de fondos españoles ni un servicio de producción.[8]

Hay discrepancia oficial: pricing dice Free 5 lookups/mes y Pro 1.000 requests/mes; requests dice Free 15 y Pro 9.000. El precio Pro de 49 USD/mes coincide, pero no la cuota. No elegir la cifra más favorable ni atribuirla a una cuenta propia inexistente.[6][15]

Free/Starter se describen para evaluación/uso personal en pricing; los términos generales permiten aplicaciones incluso comerciales. Falta aclarar el uso académico público y el alcance por plan. No se activó prueba con tarjeta ni se pidió permiso a la empresa.[6][7]

Esta síntesis **prevalece sobre la cifra única de cuotas en el informe 10**; ese informe conserva el hallazgo histórico y debe leerse con esta corrección.

## Matriz por familia y función

La tabla siguiente integra los artefactos de la ronda, no transforma todos sus tests delegados en verificaciones independientes del coordinador.

| Necesidad | Fuente / evidencia de la ronda | Campos útiles | Faltante / condición para integración |
|---|---|---|---|
| Cuentas y depósitos españoles | Informes `04-cuentas-depositos-apis.md` y `05-bancos-fichas-importables.md`; páginas/documentos primarios | TAE/TIN, tramos, promoción, mínimos, liquidez y requisitos cuando el documento los publica | Revisión por oferta; no inferir comisiones cero ni condiciones completas de un titular. YieldMeister necesita contraste. |
| Fondos tradicionales | `02-fondos-tradicionales.md`; descarga Bestinver y ficha CNMV | ISIN/registro/documentos; NAV histórico de un producto concreto | Extender por gestora/clase, permisos de almacenamiento/display, KID y costes con etiquetas originales. |
| ETF UCITS | `03-etf-emisores.md`; CSV iShares y XLSX DWS/SPDR guardados | Holdings, fecha, pesos e ISIN de posiciones cuando figuran; no son cotizaciones de bolsa | Maestro de clases/listings, KID español y licencia. No usar ficha profesional como documento minorista. |
| Letras/deuda | `07-deuda-instrumentos.md`; Tesoro, subastas y BOE | Identidad, vencimiento y resultado de evento/documento concreto según fuente | Separar subasta, referencia estadística y cotización secundaria; EOD individual autorizado pendiente. |
| Identidad de instrumentos y entidades | `06-identificadores-registros.md`, `08-catalogos-datos-abiertos.md` | ISIN/MIC/LEI, registro y entidad cuando se verifican | No equivalen a comercialización para residente español, oferta disponible ni idoneidad. |
| Contexto macro | `08-catalogos-datos-abiertos.md` | Inflación/FX/tipos por periodo y unidad | Dato mensual/histórico no llena TAE de una oferta. Separar su frescura de la comercial. |
| PostgreSQL / HTTP | `09-postgresql-ingesta-consulta.md` | Catálogo propio, versiones, consultas acotadas, PostgREST/Supabase/Neon como candidatos | Ninguna cuenta/DB creada; verificar coste, región, privacidad, pausa/cold start y API real. |
| Proveedores comerciales | `01-mercado.md`, `10-agregadores-alternativas.md` | Datos potenciales de mercado/fondos/feeds de partners | Demo USA no acredita UCITS europeo; permiso público/cache y acceso gratuito no demostrados por documentación general. |

## Arquitectura propuesta que conserva la idea PostgreSQL

`Fuentes aprobadas → adaptadores → cuarentena/revisión → catálogo PostgreSQL → API de lectura / snapshot publicado → comparador y herramientas Pai`.

PostgreSQL es el candidato de catálogo autoritativo solicitado por el grupo, condicionado a elegir alojamiento gratuito viable. Un JSON versionado puede ser **salida de publicación/caché/respaldo**, no un rechazo unilateral de la propuesta ni una fuente inventada. Si DB cloud bloquea la semana, plantear explícitamente la alternativa antes de sustituirla.

- Ingesta compartida por fuente, nunca una llamada al proveedor por visitante.
- Catálogo y perfiles separados: no guardar perfiles financieros personales en la DB común.
- Cada campo conserva valor literal/normalizado, unidad, fuente, fecha efectiva, comprobación, estado, revisión y derechos por uso.
- Las herramientas del modelo leen filas publicadas y cálculos deterministas; sin SQL libre, navegación arbitraria ni escritura.
- Publicar solo el campo y uso respaldados; desconocido no es cero, no es un permiso y tampoco demuestra que el permiso no exista.

## Pruebas decisivas pendientes

1. Seleccionar muestras medibles de las cinco familias y completar identidad, condiciones y derechos por campo/acción.
2. Resolver con fuentes primarias los conflictos detectados; no promocionar un dato del agregador por responder 200.
3. Elegir proveedor de IA y comprobar una llamada gratuita real con tools, español y condiciones de privacidad aceptables. No se hizo.
4. Elegir/autorizar cuenta y alojamiento DB; probar consultas de catálogo, permisos e ingesta idempotente. No se hizo.
5. Integrar frontend→backend→herramientas→datos y ejecutar QA/carga separada. Los verificadores aislados no cubren esa aceptación.

No hay aplicación, PostgreSQL, proveedor IA operativo ni despliegue por el hecho de completar esta investigación. No se necesitan más búsquedas genéricas: el siguiente avance útil es una prueba acotada de los candidatos y las decisiones pendientes del grupo.

## Sources

[2] https://yieldmeister.com/pricing
[3] https://yieldmeister.com/api-terms
[4] https://yieldmeister.com/api/v1/rates
[6] https://fundfactsapi.com/pricing
[7] https://fundfactsapi.com/terms
[8] https://fundfactsapi.com/api/v1/demo/funds/IE00B4L5Y983
[12] https://www.bestinver.es/WS/Api/Profitability/DownloadExcelLiquidity?productId=2
[13] https://www.openbank.es/deposito-a-plazo-fijo
[14] https://www.bestinver.es/fondos-de-inversion/bestinver-bolsa
[15] https://fundfactsapi.com/docs/requests
