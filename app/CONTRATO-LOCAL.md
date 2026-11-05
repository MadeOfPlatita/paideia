# Contrato local de implementación — Paideia

Estado: contrato del prototipo local, no API de producción. Carpeta raíz: `app/`. Sin dependencias instaladas, cuentas, red externa, datos personales reales o proveedor LLM activo. Backend Python stdlib, frontend HTML/CSS/JS local. Abrir por HTTP del backend, no file://. Carpeta estática `static/`.

## HTTP y JSON

Servidor `python app.py --port 8765` en 127.0.0.1 (port configurable). JSON UTF-8; errores `{error:{code,message,request_id,retryable:false}}`. Validar campos extra, Content-Type, tamaño y entradas. No almacenar perfiles en servidor ni loguear bodies. API y frontend mismo origen; CSP sin scripts/estilos inline y sin conexiones externas. GET assets controlados sin directory traversal. No endpoint de SQL/URL arbitraria o compra. Sin conexión externa y sin credenciales.

### GET /api/status

`{mode:"local_prototype",ai:{connected:false,status:"not_configured",message:"Chat IA no conectado. No se han enviado datos a proveedores."},catalogue:{candidate_count:20,publication_ready:0},storage:"local_snapshot_not_postgresql"}`.

### GET /api/catalogue

Parámetros opcionales `q` y `family`, enums: cuenta_remunerada, deposito, letra_deuda_publica, fondo_tradicional, etf_ucits. Respuesta `{items:[Product],count:N,not_for_publication:true}`. Fuente read-only: `docs/validacion-04/05-catalogo/candidatos.json`, nunca modificar. Products son metadatos de investigación interna, no oferta contractual ni productos listos para publicar. No copiar los campos de tasas, NAV u otros datos de la fuente con derechos pendientes. La UI debe mostrar siempre el alcance interno y la condición pendiente.

Product: `{id,name,family,issuer,isin:null|string,identity_state:"verified"|"proposed",primary_url,as_of:null|string,publication_ready:false,conditions_state:"pending",conflicts:[string],unknown_fields:[string]}`. `issuer` es la marca textual. `as_of` puede ser null si no existe una sola fecha efectiva inequívoca; no sustituir por consulta. Nunca inferir tasa, riesgo, garantía o disponibilidad.

### GET /api/products/{id}

`{product:Product}` o 404. ID lookup exacto en snapshot, sin filenames de usuario.

### POST /api/compare

Entrada `{product_ids:[id,id,...]}` de 2 a 4 IDs distintos. Respuesta `{items:[Product],comparison_kind:"educational_metadata_only",quantitative_ready:false,reasons:[string],hypothetical:false}`. Sin ranking personalizado ni rentabilidades inventadas. Si familias distintas, advertencia de diferencias de naturaleza y no ordenar numéricamente. Campos pendientes se presentan como desconocidos, nunca cero. Las herramientas de comparación no son mutaciones.

### POST /api/calculate

Entrada cerrada: `{principal:"1000.00",annual_rate_percent:"3.00",years:5,monthly_contribution:"100.00",method:"compound",inflation_percent:"2.00"}`. Decimal strings, no NaN/Infinity, years integer1..40; importes >=0 y cotas documentadas; annual_rate_percent > -100; method simple|compound. Backend documenta convención: aportación al final de cada mes; tasa anual efectiva y conversión mensual para compuesto. Interés simple sobre cada aportación según tiempo restante; nada de extrapolar promociones.

Salida `{hypothetical:true,not_prediction:true,currency:"EUR",assumptions:{...},summary:{contributions:"...",final_balance:"...",interest:"...",inflation_adjusted:"..."},series:[{month:0,contributions:"...",balance:"...",real_balance:"..."},...]}`. Series a frecuencia al menos anual y último mes; summary con redondeo centavo, no redondear mes a mes si no se declara. Siempre bruto sin fiscalidad/comisiones de producto. UI muestra inputs editables y gráfica SVG + tabla accesible, aportado separado de resultado, pérdidas posibles con tasa negativa. Valor input de rate es porcentaje (3=3%), no ratio.

### POST /api/context-preview

Entrada cerrada real `{synthetic_fixture:true,fixture_id:"synthetic-full-profile-01",purpose,selected_fields:[...],consent:{notice_version,accepted_chat_processing:true,approved_fields:[...],purpose}}`. Carga solo la fixture sintética allowlisted desde disco: rechaza perfiles aportados en el body y campos extra. El cliente real prepara vista previa local, NO envía el perfil financiero al servidor como atajo. Respuesta `{projection:<DTO04>,external_sent:false}`. El módulo `context_adapter.py` integra perfil05/proyector04/materializador03 con tests; eso no prueba un proveedor LLM. El frontend cotidiano no llama a este endpoint con su perfil.

### POST /api/chat

Siempre 503 error `CHAT_NOT_CONFIGURED`. Nada de respuestas prefabricadas como IA, ninguna llamada remota.

## Frontend

Rutas hash: #inicio, #perfil, #biblioteca, #comparar, #escenarios, #simulacion, #glosario, #privacidad. Estado en memoria; persistencia perfil solo con opt-in y botón borrar. Perfil sin nombre/DNI/banco; preguntas de una en una, omitir/no sé, resumen editable. No cambiar selección/remoto automáticamente.

La simulación usa producto candidato real como referencia identificativa y solo importes hipotéticos del usuario; si faltan condiciones, indicarlo y no generar cálculos contractuales. Confirmación/local justificante printable inequívocamente educativo, no contrato ni operación. Ninguna solicitud de pago/IBAN/identidad. No enviar la simulación al servidor.

Pruebas: HTTP local con servidor efímero, domain tests y browser smoke del recorrido. Las fixtures para test quedan bajo namespace synthetic_fixture y no se mezclan con candidates. Prototipo local incompleto respecto a catálogo publicable/IA/Postgres; reportarlo sin ocultarlo.
