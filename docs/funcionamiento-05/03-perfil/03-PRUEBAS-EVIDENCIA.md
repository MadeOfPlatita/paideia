# Pruebas y evidencia del perfil

## Automatizadas

| Comando | Resultado observado |
|---|---|
| `node --test tests/profile_model.test.cjs` | 13/13 correctas (Node built-in, sin paquetes externos) |
| `node --check static/app.js` | Exit 0 |
| `node --check static/profile_model.js` | Exit 0 |
| `python -B -m unittest discover -s tests -v` | 146/146 correctas |

Las pruebas Node cubren forma/path del modelo, `declarado`/`no_se`/`omitido`/`sin_preguntar`, cero como cadena, decimales y límites inclusivos, porcentajes, deuda, compromisos, las dos dimensiones de riesgo, validación cerrada, migración v1, persistencia desactivada sin escritura y borrado de claves actuales/anteriores.

## Navegador

Sesión aislada: `paideia-perfil05-agent`. Todas las respuestas introducidas en el perfil fueron sintéticas. Se comprobó:

- Preguntas centrales, ramas económicas y de riesgo, resumen editable, `No lo sé`, `Omitir`, campo aún no preguntado y el valor `0` mantenido como `"0"` al editar.
- Deuda `con_deuda` con saldo `0`, cuota declarada y coste `no_se`; compromiso declarado y plazo; tolerancia e impacto de pérdida aparecen por separado.
- El perfil no produjo llamadas fetch durante las respuestas, edición, guardado local, borrado ni vista previa local.
- Guardado tras checkbox explícito; la confirmación falsa conserva el permiso/copia y la confirmación verdadera revoca y borra. Para esa prueba se sustituyó `window.confirm` por respuestas sintéticas `false` y `true`; no se evaluó visualmente el diálogo nativo.
- Inicio/chat visible y no conectado sin enviar mensaje. Biblioteca, comparador, calculadora y ensayo ficticio navegaron usando respuestas sintéticas inyectadas: dos candidatos ficticios, comparación de IDs sintéticos y una serie de cálculo hipotética de ceros.
- Registro fetch posterior a la instrumentación: `/api/catalogue` GET, `/api/compare` POST con solo `product_ids`, `/api/calculate` POST con los seis campos exactos del escenario y `/api/catalogue` GET para el ensayo. Ningún body incluyó claves de perfil; 0 POST de chat, 0 llamada a `/api/context-preview`, 0 errores de consola capturados después de la instrumentación.

Archivos de evidencia, sin datos reales:

- `evidence/profile-summary-synthetic.png`: resumen con «No lo sé» y «Omitido».
- `evidence/profile-privacy-synthetic.png`: control local de privacidad tras la prueba sintética.
- `evidence/browser-network-synthetic.json`: registro estructurado en el límite de `fetch`, con fixtures, métodos, claves del body y limitaciones.

El primer `GET /api/status` ocurrió antes de instalar el interceptor de fixtures; es una consulta local sin body. No se hizo llamada a proveedor ni se envió mensaje/perfil. Las llamadas posteriores del smoke de navegación se interceptaron en navegador y respondieron fixtures; por eso no prueban la integración HTTP real. El coordinador repetirá su aceptación integrada. Las capturas documentan funcionalidad; no son aprobación visual ni se modificó CSS.
