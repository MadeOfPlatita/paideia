# Informe de la noche (2026-11-05)

Objetivo: dejar la app de Render completa y honesta. Esto es lo que se hizo, con
su evidencia, y lo que sigue abierto.

## 1. Fondos y ETF ya muestran sus datos — hecho

Antes: esas familias solo llevaban tasa y plazo, que no tienen, así que la ficha
salía vacía aunque la transcripción trajera TER, ISIN, comisiones o SRI.

Ahora `catalogue_conditions.py` traduce las métricas transcritas
(`DOCUMENTED_METRICS`) y las emite como condiciones con su URL y fecha; la ficha
las pinta con etiqueta y formato, y no genera fila vacía para lo que no conoce.

Evidencia:
- API real de Render: `GET /api/products/ETF-01` devuelve 11 condiciones —
  `isin IE00B4K48X80`, `ter_percent 0.12`, comisiones 0, `risk_scale 4/7`,
  `base_currency EUR`, `replication «pasiva (réplica del MSCI Europe Index)»`,
  `holding_period_years 5`, `depositary State Street…`— con estado `partial`.
- Navegador: la ficha del ETF muestra cada línea con «documentada por la fuente»
  y el enlace de BlackRock.
- Pruebas: `tests/test_documented_metrics.py` (6 pruebas) y el arnés de la ficha
  (`b4_ui_catalogue_provenance.test.cjs`) ampliado.

Commit `ad3bb9b`.

## 2. Perfil: se dejan de pedir las tres que no viajaban — decidido

El DTO del chat (`chat_context.py`) solo acepta objetivo, horizonte, importe y
colchón. Liquidez, tolerancia y capacidad de pérdida se guardaban y no las leía
nadie. Se marcan `asked: false`: el cuestionario pasa de 7 a **4 preguntas**
(objetivo, horizonte, experiencia e importe) y las claves siguen en el modelo
para no romper perfiles guardados.

La alternativa —enviarlas al chat con consentimiento por campo— exige subir el
aviso a `chat-context-map-v2`, tres casillas nuevas y actualizar las pruebas de
consentimiento. Queda como decisión de producto; el coste es ese, no más.

## 3. Cupo diario: documentado, no persistente — límite real

El contador vive en memoria del proceso; se reinicia al redeploy, al reinicio y
al despertar del sueño de Render. Persistirlo requiere un almacén externo con
credencial (Redis/Upstash o base de datos), fuera de las restricciones de esta
noche. Queda escrito en `docs/CUPO-Y-LIMITES.md`: qué protege (bucles, abuso
trivial), qué no (presupuesto diario global) y qué límites sí son reales
(proveedor, 10/min, 16 KB de entrada y 900 tokens de salida).

## 4. Defectos menores de la auditoría

- Rama muerta de «temas que te interesan» eliminada de `app.js` (ningún
  cuestionario define `topics` desde que Experiencia no los pide).
- `documented` deja de ser dato sin consumidor: ahora alimenta la ficha.
- Prueba nueva de que una etiqueta sin regla **no** se borra de «desconocidos»
  (`test_a_label_without_a_rule_is_never_removed`).
- El estado `partial` ya se distingue en la cabecera de la ficha («Condiciones no
  validadas para publicar»).
- `README`, `docs/INDICE.md` y `.gitignore` ordenados; rama
  `contador-mision-pendiente` para lo no aprobado.

## 5. Pruebas

- `python -m pytest tests -q` → 691 aprobadas.
- `node --test tests/*.test.cjs` → 108 aprobadas.
- Puerta completa (`tools/quality_gate.py`) → exit 0.

## 6. Límites que siguen en pie

- El catálogo no es publicable: faltan permisos y verificación de vigencia.
- El texto del modelo no se valida semánticamente; solo las citas y los cálculos.
- La demo duerme a los 15 minutos sin tráfico.
- Cualquiera con el enlace puede gastar el cupo del proceso.
