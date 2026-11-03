# Prototipo aislado: proyección de perfil remoto

**Estado: contrato y verificador aislados; integración pendiente.** Este directorio no modifica el perfil local 05, la aplicación, la base de datos, cuentas ni despliegue. No se ha configurado ni llamado a ningún proveedor; no se creó cuenta ni registro para esta prueba.

## Decisión de diseño del prototipo

El perfil local de `05-perfil-conversacion/perfil.schema.json` sigue siendo rico, local y distinto del DTO remoto. La función de producción `project_profile(profile, purpose=..., selected_fields=..., consent=...)` crea un objeto nuevo usando una lista blanca explícita de campos y reglas por propósito. No convierte el perfil entero a diccionario, no lo serializa ni incluye automáticamente campos no seleccionados.

La autorización exige `accepted_chat_processing is True`, propósito coincidente y que `consent.approved_fields` coincida exactamente con la selección vigente. Si se retira un campo después de consentir, se rechaza la solicitud completa: no se conserva una selección obsoleta ni se envía un subconjunto silencioso. No llamar al proyector si el usuario no quiere contexto de perfil.

El prototipo **no decide que todo dato financiero deba quedar prohibido**. Admite, con selección explícita, propósito y consentimiento, conocimiento/experiencia, objetivos, liquidez, horizonte, tolerancia y capacidad de pérdidas, ingresos/gastos, deuda, colchón y compromisos próximos. Las cifras se transmiten como cadenas decimales exactas en EUR; el benchmark debe decidir si una tarea realmente necesita cada cifra. La comparación entre contexto selectivo y completo sigue pendiente.

## Contratos

- `profile-projection.schema.json`: DTO remoto selectivo, cerrado (`additionalProperties: false`), con campos permitidos por propósito. Cada respuesta conserva `known`, `unknown`, `omitted` o `not_asked`; los estados sin declarar no llevan `value`.
- `projection-consent.schema.json`: autorización cerrada, con propósito y lista de campos aprobados. El schema permite representar un rechazo; la función no proyecta si el consentimiento no es `true`.
- `synthetic-benchmark-projection.schema.json`: contrato distinto e incompatible con el DTO de producción; exige todos los campos y etiqueta `synthetic_benchmark_only`.
- `MAPPING.md`: mapping español 05 ↔ DTO, estados, unidades y excepciones.

Este DTO no es el `ProfileContext` de `01-pai-tools/contratos.json` ni se puede copiar allí sin un adaptador/versionado explícito. En particular, un `share_profile_with_model` genérico no sustituye la autorización por propósito y lista exacta de campos de este prototipo.

`project_profile` no tiene un parámetro genérico `full`/`mode`. La variante completa está separada en `project_synthetic_full_for_benchmark`, requiere un envelope `synthetic_fixture` y el ID de fixture allowlisted `synthetic-full-profile-01`, y produce el marcador no productivo `synthetic_benchmark_only`. La fixture incluida es enteramente inventada y solo sirve para ensayar contratos; la etiqueta y el ID son controles de harness, no una prueba criptográfica de procedencia. No se debe conectar esta función al envío de producción.

El campo local `supuestos_escenario` se excluye: el schema 05 aclara que son entradas hipotéticas, no respuestas del perfil. `sin_deuda` se conserva como `situation=no_debt`; una deuda declarada cuyo saldo sea `0` sigue siendo `has_debt` con importe `"0"`; una respuesta desconocida/omitida/no preguntada no se convierte en cero ni en deuda inexistente. En rangos EUR, `max_eur: null` conserva el significado local de límite superior abierto, no de cifra desconocida.

## Uso y precisión

La función es pura y depende solo de la biblioteca estándar. Como el schema local 05 representa importes JSON como `number`, el llamador debe parsear decimales sin pasar primero por `float`, por ejemplo:

```python
import json
from decimal import Decimal
from profile_projection import project_profile

profile = json.loads(profile_json_text, parse_float=Decimal)
consent = {
    "notice_version": "notice-v1",
    "accepted_chat_processing": True,
    "purpose": "debt_education",
    "approved_fields": ["debt", "monthly_expenses_eur"],
}
payload = project_profile(
    profile,
    purpose="debt_education",
    selected_fields=["debt", "monthly_expenses_eur"],
    consent=consent,
)
```

Se rechazan `float`, booleanos, valores no finitos y escalas negativas para cifras financieras; se devuelve `Decimal` como string fijo sin redondeo (se preservan ceros decimales significativos). El caller todavía debe validar el perfil local contra el schema 05 y validar el payload contra el schema remoto antes de cualquier integración.

## Privacidad: límites

La lista blanca controla únicamente los campos estructurados que construye este módulo. No filtra el mensaje libre del usuario ni promete detectar PII con infalibilidad: texto libre puede contener nombres, cuentas u otros datos identificativos. La política de mensaje, aviso, vista previa visible, retención y revisión del proveedor siguen pendientes. No incluir el objeto local ni historial completo como atajo.

## Pruebas locales

Desde este directorio:

```sh
python -m unittest -v
```

Las pruebas usan `unittest` y los módulos `jsonschema`/`referencing` que ya estén disponibles para verificar schemas y referencias URN locales; no instalan nada ni hacen llamadas de red. `profile_projection.py` no depende de esos paquetes. Se han ensayado consentimiento, selección retirada, extras, propósito, decimales, estados, distinción de deuda, no mutación, selección efectiva, y separación del benchmark sintético.

## Integración pendiente — no declarada resuelta

1. Integrar primero la revisión local del perfil 05, el selector visible por propósito, preview exacto del payload y retirada de campos; el consentimiento no puede inferirse de una preferencia genérica.
2. Validar localmente la solicitud y después el DTO proyectado. No enviar datos financieros reales hasta completar revisión de proveedor, términos, retención, exposición, seguridad y aviso. Presupuesto del proyecto: 0 EUR, sin tarjeta ni overage.
3. Ejecutar benchmark **solo sintético** con las variantes sin perfil / proyección selectiva / perfil completo, mismos casos, prompt, proveedor/modelo y herramientas. Evaluar calidad, errores críticos, utilidad educativa, tokens/coste y minimización; no hay ganador ni decisión de producto en este prototipo.
4. Decidir con el grupo la variante final y si las cifras son aceptables por propósito/tarea. No usar el resultado del benchmark sintético como autorización para datos reales.
5. Revisar cómo borrar el perfil local y qué puede/no puede borrarse en el proveedor. No prometer eliminación de copias remotas sin garantías verificadas.

No se han ejecutado integraciones, benchmark de modelos, revisión legal/proveedor ni pruebas con personas o perfiles reales.
