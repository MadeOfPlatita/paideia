# B9 · ciclo 2 — corrección de la revisión independiente

Fecha: 04/11/2026. Ámbito: `prototipos/paideia-local/static/{app.js,styles.css,comparison_report.js}` y copia `api/_static`. Sin red externa, sin `.env`, sin commit.

## Correcciones

| Defecto | Cambio | Evidencia |
|---|---|---|
| D1 · foco en BODY al reintentar | `focusResultsRegion()` conserva el foco si estaba dentro del contenedor que se reemplaza: `#scenario-output[tabindex=-1]`, el botón de reintento si vuelve a fallar, o `#simulation-product` cuando reaparece | `app.js:2020-2038`, `app.js:2468-2477` |
| D2 · chip obsoleto | Un éxito de API durante una comprobación de estado en vuelo habilita **un** reintento automático de `/api/status` a los 1,5 s si esa comprobación falla; si el reintento falla, no se repite | `app.js:2836-2904` |
| D3 · envío vacío sin aria-invalid | `novalidate` en el formulario de escenarios y en el del importe del ensayo: el envío vacío llega a la validación propia, que marca `aria-invalid`, asocia el mensaje inline y enfoca el campo | `app.js:2331`, `app.js:2615` |
| D4 · palabras partidas y 3 px | Guiones suaves en las etiquetas del stepper y reflujo de topbar/nav | `app.js:2431-2433`, `styles.css:123,132,372,377` |
| D5 · región viva reescrita | `setText()` solo muta la región `role=status` del informe si el texto cambia | `comparison_report.js:215,223-224` |
| D6 · foco perdido al deshabilitar | El foco pasa a `#scenario-output` antes de `submitButton.disabled = true` | `app.js:2260-2264` |

## Pruebas nuevas (rojo antes, verde después)

`tests/b9_accessibility.test.cjs`: B9-3c, B9-3d (D1), B9-11b (D2), B9-5d, B9-5e (D3), B9-6c (D4), B9-7b (D5), B9-9c (D6). Total 32 comprobaciones.

Copia previa del ciclo 2 (solo para la prueba, restaurada después) con
`B9_ONLY=B9-3c,B9-3d,B9-5d,B9-5e,B9-6c,B9-7b,B9-9c,B9-11b`:

```
FAIL B9-3c  during=BODY after=BODY
FAIL B9-3d  after=BODY
FAIL B9-5d  Timeout esperando error de envío vacío
FAIL B9-5e  Timeout esperando error de importe vacío
FAIL B9-6c  scrollWidth=334 nav=["02Biblioteca","03Comparar","04Escenarios","06Glosario","07Privacidad"]
FAIL B9-7b  reportMutations=5
FAIL B9-9c  during=BODY after=BODY
FAIL B9-11b Timeout esperando chip recuperado sin interacción
```

Con el código actual:

```
node tests/b9_accessibility.test.cjs
Resumen: 32 comprobaciones, 32 PASS, 0 fallo(s) de producto, 0 fallo(s) de arnés.
ESTADO: VERDE
```

## Resto de la suite

- `node tests/b8_privacy_regression.test.cjs` → 28/28 PASS.
- `node tests/b1_history_consent.test.cjs` → 59 PASS + 2 observaciones, 0 fallos.
- `node tests/*.test.cjs` en `prototipos/paideia-local` → 63 comprobaciones, 0 fallos.
- `python -m pytest tests -q` (cwd `prototipos/paideia-local`) → 544 passed, 453 subtests, 61,13 s.
- `diff -rq prototipos/paideia-local/static api/_static` → sin diferencias; `cmp` y sha256 idénticos para `app.js`, `index.html`, `styles.css` y `comparison_report.js`.

## Límite de D4

A 320 px y 200 % simultáneos la retícula de cinco columnas deja 58 px por paso: las etiquetas largas se parten en varias líneas. La comprobación inicial midió `scrollWidth=320` e `innerWidth=320`, pero por sí sola no demuestra ausencia de scroll: la revisión final midió `clientWidth=305` con barra clásica de escritorio y documentó 15 px de desplazamiento horizontal residual. En la emulación móvil midió 320/320. Ver `REVISION-CICLO-2.md`.

Nota de entorno: en Chrome headless con barras de desplazamiento clásicas, `html{min-width:320px}` (preexistente, sin cambios) mantiene 15 px de diferencia entre `scrollWidth` y `clientWidth` a 320 px; no es el desbordamiento de 3 px de topbar/nav y queda fuera de este ciclo.
