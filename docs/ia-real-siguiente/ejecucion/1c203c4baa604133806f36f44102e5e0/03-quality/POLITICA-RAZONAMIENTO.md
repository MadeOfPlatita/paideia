# Política de petición para el nuevo bloque

Fuente pública consultada: https://console.groq.com/docs/reasoning y https://console.groq.com/docs/model/openai/gpt-oss-20b.

La documentación confirma reasoning_effort low/medium/high para GPT-OSS e include_reasoning:false para excluir el campo de razonamiento (no combinar con reasoning_format). Se fija low y no devolver reasoning en ambos modelos ya permitidos y en todas las variantes del benchmark, sin subir max_tokens256 ni cambiar el modelo. No se afirma que esto reduzca exactamente tokens/coste ni resuelva el truncado: pendiente prueba real autorizada. No demuestra la causa del incidente anterior.

TDD: el nuevo test de petición falló sin política; se actualizó expectativa exacta del contrato anterior, no se debilitó. Otra prueba detectó discrepancia de las18solicitudes planificadas con el constructor nativo; se alinearon campos y bytes. Pruebas propias y del proveedor correctas. Aún cero llamadas reales de esta misión.
