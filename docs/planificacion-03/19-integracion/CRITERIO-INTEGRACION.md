# Integración de la planificación — criterio del coordinador

**Estado: diseño consolidado, implementación e integración pendientes.** Este documento resuelve la precedencia entre propuestas de los frentes 01–16 y las auditorías 17–18. No convierte sugerencias en decisiones del grupo ni declara aprobados proveedor, alojamiento, permisos o funciones aún no construidas. `docs/REQUISITOS.md` sigue mandando sobre el alcance.

## Precedencia y arquitectura

1. Requisitos aprobados del grupo.
2. Este criterio de integración y la síntesis de APIs `../../investigacion-apis-02/00-SINTESIS.md` para los contrastes nuevos.
3. Especificaciones de cada frente, con sus notas de corrección.
4. Auditorías históricas como evidencia de lo detectado; sus alternativas no se adoptan automáticamente.

`Fuente → adaptador → cuarentena → aprobación de publicación → catálogo PostgreSQL propuesto → API/snapshot versionado → UI y tools Pai`.

El servidor selecciona y valida herramientas; el modelo no ve credenciales ni ejecuta SQL. PostgreSQL sigue siendo candidato de catálogo autoritativo: se propone alojamiento administrado gratuito si supera las pruebas. JSON es salida de publicación/caché/respaldo; usarlo como sustituto total exige informar al grupo, no descartar silenciosamente la DB. No crear servicios ni instalar hasta autorización correspondiente.

## Disposición de los ocho hallazgos de contratos

| Hallazgo | Resolución de diseño | Estado real / prueba de cierre |
|---|---|---|
| PAI-CROSS-01: consentimiento y perfil | Un turno remoto exige `accepted_chat_processing=true`. Rechazo se gestiona localmente, sin llamada. Perfil local completo distinto de proyección remota seleccionada y mostrada antes de enviar. No autorizar cifras solo por `share_profile_with_model=true`. | **Corregida y probada la condición de consentimiento** en el schema 01: una regresión falló antes y pasa después. La proyección remota y la decisión de enviar cifras siguen pendientes; el objeto rico ProfileContext no se puede serializar directamente. |
| PAI-CROSS-02: tools y allowlist | Cinco nombres canónicos del contrato 01: `search_products`, `get_product_detail`, `compare_products`, `calculate_scenario`, `get_sources`. Lectura y cálculo puro, no agencia de escritura. El ejemplo de dos tools en español del frente 08 no es la nueva allowlist. | Manifest propuesto en este directorio; apagado hasta pasar seguridad/proveedor, **no pospuesto fuera del MVP como cambio de alcance**. Falta implementar dispatch y probar input/output/IDs contra filas publicadas. |
| PAI-CROSS-03: IDs y familias | UUIDv4 estable para producto/clase/listing y fuente públicos; identidad externa namespaced literal en tabla aparte. Emisor/entidad, clase, listing, oferta y observación son entidades distintas. | Mapping abajo. Asignar claves mediante persistencia, no UUID aleatorio por consulta ni conversión de ticker a identidad. Falta DB/migración y prueba de estabilidad/idempotencia. |
| PAI-CROSS-04: escalas | `PERCENT: "3.00" = 3 %`; ratio `"0.03" = 3 %`. API financiera en decimal string; NUMERIC/Decimal para dinero. `annual_rate_percent` se divide por 100 exactamente una vez; r de fórmula es ratio. | Regla resuelta documentalmente; falta adaptador ejecutable y tests extremo a extremo. Los floats del demostrador 06 no son DTO monetario de producción. |
| PAI-CROSS-05: fechas y null | Conservar precisión fecha/instante; `retrieved_at` UTC no reemplaza observación/validez. Hecho público admite null con estado y motivo; nunca convertir desconocido en cero. Versión de frescura explícita. | El schema 14 actual **todavía no representa hechos desconocidos con null**: no usarlo como schema público final. Parche/migración de su contrato y fixtures pendientes antes de conectar. No se declara resuelto en código. |
| PAI-CROSS-06: citas y códigos | Campo y decisión enlazan `fact_id → source_revision → source_id + locator/hash`. Mantener códigos existentes del comparador y su clase CONTROL/EDUCATIONAL; no exigir prefijo CONTROL_ inexistente. | Corrección textual de la regla de namespaces; falta propagación de fact refs en DTOs/handlers y prueba de trazabilidad. No inventar fact_id ni enlaces desde la explicación del modelo. |
| PAI-CROSS-07: errores | Contrato HTTP no-2xx separado del éxito 2xx. Envelope seguro de 08 como base: request_id, código, mensaje, retryable y retry_after_seconds. No hacer pasar fallo HTTP por ConversationTurnResponse. | Mapping abajo; falta schema unificado del envelope y adaptadores/test HTTP. No reenviar respuestas upstream, SQL o prompts en errores. |
| PAI-CROSS-08: escenarios | `calculate_scenario` conserva interés simple/compuesto. Laboratorio avanzado tiene DTO separado, flujos/fechas/costes/inflación y hypothetical=true. | No convertir el contrato simple a laboratorio perdiendo datos. Falta DTO/UI integrados; ejemplos sintéticos continúan aislados, nunca catálogo real. |

## Mapping de identidad y observaciones

| Origen adapter | Destino autorizado con evidencia | Lo que NO implica |
|---|---|---|
| deposit_offer | Cuenta remunerada o depósito, según naturaleza contractual documentada | No inferir familia solo de tasa/plazo/nombre. |
| public_debt_observation | Subasta, serie o cotización con tipo de observación explícito; enlazar instrumento identificado si lo hay | Una serie estadística o resultado de subasta no es cotización secundaria ni oferta contratatable. |
| fund_share_class | Clase con ISIN exacto; mutual_fund/etf según evidencia del vehículo | No clasificar todo fondo cotizado/registrado como ETF por ticker o marca. |
| market_listing | Listing hijo de clase, con bolsa/MIC, ticker, moneda de negociación | No confundir moneda de clase y de listing, ni NAV y precio de mercado. |
| legal_institution | Entidad/emisor/gestora/depositaria | No crear producto financiero desde una ficha registral. |

Un hecho canónico propuesto contiene: `fact_id`, `field_path`, `value|null`, `state`, `reason|null`, `unit`, `currency|null`, `observation{value,precision}`, `valid_from/to`, `retrieved_at`, `source_revision_id`, `locator`, `freshness_policy_version`. `unknown`, `not_applicable`, `conflict` y `known` son estados diferentes. Un conflicto puede conservar observaciones fuente separadas con valores conocidos, pero no seleccionar una como cierta automáticamente.

La política de frescura se versiona por campo y uso. La consulta diaria es frecuencia de chequeo, no certificado de actualidad. TTL/hábitos de días hábiles y exclusiones comerciales requieren configuración y validación; no copiar valores de `test_only_policy` a producción.

## Errores públicos propuestos

| Situación | HTTP | Código público / traducción | Reintento |
|---|---|---|---|
| Consentimiento ausente/rechazado | 403 | CONSENT_REQUIRED | No automático |
| Payload inválido / argumento extra | 400 | INVALID_REQUEST / INVALID_TOOL_CALL | Corregir antes |
| Producto o fuente no publicados/inexistentes | 404 | PRODUCT_NOT_FOUND / SOURCE_NOT_FOUND | No automático |
| Cuota sesión | 429 | SESSION_LIMIT → RATE_LIMITED en UI | Mostrar espera; no retry automático |
| Capacidad global / proveedor apagado | 503 | GLOBAL_CAPACITY / CHAT_DISABLED → MODEL_UNAVAILABLE | Estado visible; catálogo no depende del chat |
| Timeout proveedor | 504 | PROVIDER_TIMEOUT → MODEL_UNAVAILABLE | Entrega incierta; no reenviar automáticamente |
| Respuesta inválida proveedor | 502 | PROVIDER_RESPONSE_REJECTED → INVALID_MODEL_RESPONSE | No mostrar payload bruto |

Los aliases de UI no sustituyen código original seguro, request_id ni Retry-After. Un nuevo intento manual también pasa por cuota/consentimiento. La implementación puede refinar status/códigos con tests, pero debe actualizar la tabla y schema juntos.

## Perfil y privacidad: sin reducción silenciosa

- Se conserva perfil financiero local y editable: conocimientos, tolerancia y capacidad, ingresos/gastos/deudas y objetivos según relevancia; omitir/no saber sigue permitido.
- La política C09 original que solo permitía preferencias no financieras **locales** no reemplaza ese requisito. Se corrige como criterio de diseño, no se afirma que exista ya un almacén seguro.
- Persistencia local opt-in y borrado; no registro ni nombre/DNI/banco/credenciales. Las cifras locales no son anónimas por estar en un navegador.
- Proyección remota mínima: campos educativos seleccionados y mensaje, tras aviso y preview. Importes/deudas solo si el grupo aprueba esa experiencia y se cierran proveedor/condiciones/retención; esa aprobación de producto no sustituye el control por petición del usuario final.
- No adjuntar perfil/historial completos por defecto. El schema rico de 01 no demuestra minimización ni autoriza todo su contenido. Probar que un campo desmarcado no sale, que un campo desconocido se rechaza y que borrar local no promete borrar copias del proveedor.

## Chat, tools, capacidad y coste cero

El chat LLM real contextual sigue siendo requisito; no se acepta FAQ o stub como equivalente. Sin proveedor/configuración/pruebas, está bloqueado, no terminado ni eliminado. Catálogo, comparador, glosario y cálculo deben funcionar independientemente.

Manifest cerrado, argumentos y resultados validados y límites server-side. Máximo inicial **un ciclo de herramienta por turno**: primera respuesta de selección, cálculo/lectura y una respuesta final. No significa una única llamada al modelo. Propuesta de búsqueda limitada a cinco resultados y comparación de hasta cuatro productos; los límites más amplios del schema 01 son techos estructurales, no permiso para saltarse el presupuesto runtime.

Se revisaron los escenarios del modelo local `03-capacidad-ia/scenarios.json`: para 100 usuarios, tres turnos, lean, 250 tokens y un loop/turno, son **600 peticiones al modelo**. El caso Cloudflare 3B consume aritméticamente 7.252,125 Neurons de 10.000, pero **tools no figuran confirmadas para ese modelo**. El 70B con tools documentadas excede su cuota con 44.433,75 Neurons; Groq 20B/120B supera su TPD de referencia. Son salidas del simulador, no medidas ni cuotas de cuenta verificadas. No elegir el 3B solo porque cabe en la cuenta aritmética.

Presupuesto 0 EUR estricto; sin facturación automática, tarjeta o overage. Límites por sesión efímera y global, cola justa y off-switch; IP no es identidad bajo NAT. Ninguna cifra de concurrencia, latencia o calidad está demostrada. Mistral sigue candidato abierto según contraste del coordinador del frente 02, no aprobado ni descartado por la matriz antigua.

## Ruta de construcción propuesta y puertas

1. Congelar DTOs compartidos y adaptar los schemas pendientes; mantener pruebas de referencia y añadir los mappings anteriores con tests.
2. Obtener muestras de productos reales y matriz de permiso/campo/acción; confirmar catálogo mínimo con el grupo. No completar cuotas inventando productos.
3. Con autorización, probar proveedor gratuito con mensajes sintéticos y tools reales acotadas; revisar condiciones de procesamiento. Si falla, registrar bloqueo, no fingir IA.
4. Elegir/autorización de hosting y PostgreSQL gestionado; probar permisos, API y publicación/cache. Nada depende del PC apagado del equipo.
5. Construir recorrido Pai→perfil→biblioteca→comparador→escenario→contratación ficticia. SVG+tabla accesible; impresión/PDF opcional después de validar lo esencial.
6. QA E2E, móvil/teclado y recuperación; carga frontend/catálogo/stub por separado de smoke IA autorizado. Solo declarar capacidad comprobada por capa.

La semana es objetivo del grupo, no una garantía tras sumar propuestas. No se han ejecutado estos seis pasos de aplicación.

## Verificación realizada y pendiente

En `PRUEBAS-REPRODUCIDAS.json`: 29 tests del motor, seis de capacidad, cuatro de consentimiento pasan; tres escenarios reproducidos; ingesta sintética: siete casos/diez registros/un rechazo esperado y ninguna fixture publicable. En `VALIDACION-SCHEMAS.json`: seis meta-schemas comprobados y referencias locales resueltas. Ninguno prueba backend/DB/LLM/seguridad desplegados.

Las auditorías 17/18 tienen ocho hallazgos cada una; los ocho defaults y cinco decisiones del JSON de coherencia son propuestas, no aceptación humana. La recepción/auditoría documental queda verificada; los defectos de contratos pendientes permanecen explícitos en esta disposición.
