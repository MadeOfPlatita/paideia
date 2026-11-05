# Ayuda contextual: evidencia de módulo

Ámbito: fixture sintético en navegador real, sin integración de rutas. No se ejecutaron conexiones externas, modelos ni datos personales. El servidor fue `python -m http.server 18764 --bind 127.0.0.1` desde `app` y el fixture `/tests/context_help_fixture.html`.

## TDD

Primer test antes de implementar: `FAIL existe API pública y seis definiciones cerradas: falta ContextHelp.mount/createHelp`. Tras implementar: `PASS existe API pública y seis definiciones cerradas`. Las pruebas adicionales se añadieron después de esa primera implementación, no se afirma que cada una haya pasado por RED.

## Navegador: fixture sintético

```
PASS existe API pública y seis definiciones cerradas
PASS mount crea ayudas independientes con controles accesibles
PASS abrir y cerrar restaura el foco
PASS Escape cierra y restaura el foco
PASS las entradas desconocidas se rechazan sin inserción parcial
PASS createHelp devuelve un elemento independiente
status: pass
```

Eventos reales CDP en el fixture: Space → `aria-expanded=true`; Tab → foco en `Cerrar ayuda: TAE`; Escape → `aria-expanded=false`, foco en `Ayuda: TAE`. Enter con evento `char` → `aria-expanded=true` y panel visible. No sustituye una auditoría con lectores de pantalla.

## Comprobaciones adicionales

`node --check static/context_help.js && node --check tests/context_help_test.js`: sin errores. `node --test tests/profile_model.test.cjs tests/structured_education_ui.test.cjs`: 17 pruebas, 17 aprobadas. No se ejecutó toda la suite por las restricciones de GUI/red/datos.

## Contrato y propuesta de integración (pendiente)

Cargar CSS y JS locales antes de `app.js`. `window.ContextHelp.definitions` es objeto cerrado y congelado `{clave: {label, definition}}`; claves: `tae`, `tin`, `liquidez`, `riesgo`, `inflacion`, `interes-compuesto`. Reutilizar el mismo objeto para construir el glosario. `ContextHelp.createHelp(clave)` devuelve un `span` desconectado y rechaza claves desconocidas con `RangeError`; insertar junto al término existente sin meter el botón dentro de otro botón o enlace. `ContextHelp.mount(root, {terms: [clave, ...]})` añade ayudas y devuelve array de elementos; valida todas antes de añadir y rechaza claves desconocidas. Si una vista se vuelve a renderizar, crear nuevos elementos en su nuevo contenedor. Disclosures en línea no modales: no se mueve el foco al abrir; Escape o Cerrar devuelven el foco al activador.

Sugerencia: colocar ayudas en cabeceras/etiquetas relevantes de biblioteca, comparación, escenarios y simulación solo donde aparezcan esos conceptos. Sustituir los textos duplicados del glosario por `definitions`; conservar aviso de que no es asesoramiento y verificar las condiciones de cada producto. Este trabajo no modifica `app.js`, `index.html` ni estilos compartidos. Integración real y verificación de rutas pendientes del agente principal.
