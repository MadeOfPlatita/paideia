# Adaptador local de contexto — perfil 05, proyector 04 y arnés 03

Estado: adaptador local, determinista y offline. No modifica `app.py`, el perfil de producción, las fuentes 03/04 ni el frontend. No hace llamadas de red, no almacena perfiles ni prueba calidad de modelos.

## Interfaz pública

### `preview_synthetic(payload)`

```python
preview_synthetic(payload: Mapping[str, Any]) -> dict[str, Any]
```

Payload cerrado y obligatorio:

```json
{
  "synthetic_fixture": true,
  "fixture_id": "synthetic-full-profile-01",
  "purpose": "liquidity_planning",
  "selected_fields": ["objective", "target_amount_eur"],
  "consent": {
    "notice_version": "demo-v1",
    "accepted_chat_processing": true,
    "purpose": "liquidity_planning",
    "approved_fields": ["objective", "target_amount_eur"]
  }
}
```

No se acepta `profile` en el payload. El adaptador carga por sí mismo `docs/validacion-04/04-contexto/fixtures/synthetic-full-profile.json`, comprueba la clasificación y el ID allowlisted y parsea los decimales con `Decimal`. Así no confía en un perfil remitido por el cliente ni intenta demostrar identidad mediante un ID. Si `synthetic_fixture` no es exactamente `true`, el ID no coincide, falta un campo o hay campos adicionales, rechaza la entrada.

Resultado exitoso exacto: `{ "projection": <DTO04>, "external_sent": false }`. Invoca `profile_projection.project_profile`; no llama al proyector de benchmark completo. `purpose`, `selected_fields` y `consent` se validan como objetos cerrados y se someten además a las reglas reales del proyector 04: propósito conocido, campos permitidos para ese propósito, consentimiento aceptado y coincidencia exacta de propósito/campos aprobados.

Para el backend, el handler de `POST /api/context-preview` debe llamar a esta función solo con el payload sintético anterior; no debe aceptar ni reenviar `profile`. El endpoint debe seguir siendo una demostración sintética y no una ruta del perfil real. Este encargo crea el adaptador; no integra ni habilita el handler HTTP.

### `build_context_request(...)`

```python
build_context_request(
    profile: Mapping[str, Any],
    purpose: str,
    selected_fields: list[str],
    consent: Mapping[str, Any],
    question: str,
    variant: str = "B",
) -> dict[str, Any]
```

Valida consentimiento/selección con 04, produce el DTO y crea explícitamente un `dataset` y un `case` compatibles con `pai_context_benchmark.materialize_request`. Carga el módulo 03 desde su ruta local aprobada mediante `importlib`, valida el dataset original y reutiliza su contrato de mensajes/base/hash. No modifica el dataset ni escribe requests.

- **A:** `messages` no incluye campos ni valores del perfil; `profile_context.data` es `null`.
- **B:** `messages` incluye solo el DTO de los campos seleccionados y autorizados. `profile_context` conserva metadatos de auditoría separados: estado, selección y nombres/razones de exclusión; no incluye valores de campos no seleccionados. `messages` no contiene metadatos de auditoría.
- **C:** ruta solo de benchmark sintético. Se exige que `profile` sea tipológicamente idéntico en estructura y valores a la fixture autorizada; entonces se usa `project_synthetic_full_for_benchmark`. No hay un booleano `full` que habilite proyección completa y C no está disponible en `preview_synthetic`.

Las tres variantes comparten `base`, `base_sha256`, la instrucción de sistema y la pregunta/evidencia fija; solo varía la inclusión de contexto. La salida de 03 declara `provider_call_status="not_called"`. La función construye mensajes en memoria: no los envía ni los persiste. El texto libre `question` se limita a 4000 caracteres, pero no se limpia ni se certifica como libre de datos personales; el consumidor debe tratarlo como entrada no confiable y no transmitirlo sin una vista previa/decisión separada.

Los errores controlados son `AdapterError(ValueError)`, con atributos `code` y `message`, para que la API los traduzca a su contrato de error. Códigos principales: `INVALID_PAYLOAD`, `SYNTHETIC_FIXTURE_REQUIRED`, `FIXTURE_NOT_ALLOWLISTED`, `CONSENT_INVALID`, `PROJECTION_INVALID`, `VARIANT_INVALID` y `QUESTION_INVALID`.

## Compatibilidad y límites del mapping 03

El esquema del perfil de benchmark 03 y el DTO 04 no son campos intercambiables. El adaptador **no** inventa conversiones al perfil legacy de 19 campos de 03: el caso compatible usa como `profile_fields` los 13 nombres del DTO 04 y copia esos DTO sin convertirlos. Así se preservan estados, rangos y cadenas decimales; evita aparentar equivalencias. El `prompt_contract` y la materialización A/B/C proceden de 03.

El perfil legacy de `dataset.json` contiene 19 campos; estos no pueden mapearse sin pérdida al DTO 04:

| Campo 03 | Límite del DTO 04 |
|---|---|
| `age_band`, `education_level` | No tienen campo equivalente. |
| `currency` | Los importes 04 llevan `currency: EUR`, pero no existe un campo de moneda global. |
| `financial_goal` | `objective` es una enumeración cerrada, no conserva texto libre ni todos los matices. |
| `investment_horizon_months` | `horizon` es una categoría temporal, no un número exacto de meses. |
| `liquid_savings_eur` | `liquid_reserve_eur` es un rango y no se declara semánticamente igual a todos los ahorros líquidos. |
| `monthly_net_income_eur`, `monthly_expenses_eur` | 04 conserva rangos y periodicidad, no un escalar mensual exacto. |
| `monthly_savings_capacity_eur` | No existe; no se deriva restando ingresos y gastos. |
| `planned_contribution_eur` | No existe; no se infiere de otros importes. |
| `upcoming_expenses` | `upcoming_commitments` no conserva etiquetas, lista de gastos individuales ni plazo exacto en meses. |
| `debts` | `debt` tiene otro contrato; no representa sin pérdida una lista de obligaciones individuales del benchmark. |
| `risk_tolerance` | Hay una escala cualitativa distinta; no se convierte a `low/moderate/high`. |
| `risk_capacity` | 04 conserva impacto en un escenario explícito; no se convierte a una etiqueta de capacidad. |
| `emergency_reserve_target_months` | No existe en el DTO. |
| `employment_income_stability` | No existe en el DTO. |
| `investment_experience` | `learning_level`/`learning_topics` no son equivalentes exactos ni conservan las categorías 03. |
| `knowledge_level` | No existe; no se sustituye por nivel de experiencia/interés. |
| `declared_loss_limit_pct` | No existe; impacto ante una caída no equivale a un límite porcentual. |

Por ello, los nombres originales de 03 aparecen solo en esta documentación, no en una conversión de datos. El adaptador tampoco deriva ahorro disponible, gasto, capacidad de pérdida ni elegibilidad.

## Precisión, estados y límites de seguridad

- La fixture se parsea con `parse_float=Decimal`; 04 produce cadenas decimales exactas (p. ej. `2500.00`) y rechaza floats. No hay redondeo ni normalización a `float` en este adaptador.
- Estados (`unknown`, `omitted`, `not_asked`) permanecen distintos de un valor declarado cero; deuda conocida cero y ausencia de deuda siguen siendo formas distintas según DTO 04.
- El proyector solo lee los campos seleccionados en A/B; no se serializa el objeto 05 completo. C es una excepción limitada a la fixture y al arnés local.
- Se valida el consentimiento y selección vigentes en cada llamada. Un campo retirado deja de coincidir con `approved_fields` y se rechaza.
- “Sintético” o un ID de fixture no es prueba criptográfica. No se admiten datos reales en el endpoint de vista previa. La salida del builder puede contener los campos B seleccionados en memoria; este módulo no proporciona cliente LLM ni una vía de transmisión.

## Verificación

Tests conjuntos: `python -B -m unittest discover -s app/tests -p test_context_adapter.py -v`. Cubren preview sin sockets de red, allowlist y rechazo de perfiles enviados, consentimiento/campo retirado, campos cerrados, igualdad de base A/B/C, selección B, ausencia A, C limitado a fixture, no mutación, cifras exactas y desconocido distinto de cero.

Estas pruebas verifican el acoplamiento local y la preparación de requests. No prueban un proveedor, calidad de LLM, seguridad de una llamada remota, conformidad jurídica ni integración HTTP desplegada.
