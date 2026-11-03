# Correcciones acotadas de interfaz

Navegador aislado `fix-layout-172201`, servidor existente 127.0.0.1:8765; datos ficticios. No se utilizó la sesión de preview del usuario. No se alteraron fórmulas ni persistencia.

## Evidencia
- `red-390.json`: cinco comprobaciones fallan antes del código de producción; Home client 390 / scroll 448, spans hasta 448,17 y 430,11. `home-red.png` captura el desbordamiento.
- `green-390.json`: cinco pasan; client y scroll 390, ambos spans hasta 345. `home-green.png` captura la corrección.
- `green-desktop.json`: cinco pasan, ancho configurado 1440, client y scroll 1425.
- `reload.json`: filtro depósito y selección 4/4 desaparecen tras Page.reload real; el aviso lo anticipa. El intento preliminar de navegar al mismo hash no era una recarga y no se usó como evidencia.
- `consumer-c.json`: 27 comprobaciones pasan, incluidas longitud raw 101 y ciclo del diagnóstico. `consumer-scenario.json`: 114 pasan, incluidas invalidación, errores, respuesta tardía y snapshot aislado.
- Ejecución: IIFEs de `tests/qa_layout_browser.js`, `tests/c_integration_browser.js` y `tests/scenario_browser.js` evaluadas en el documento real por CDP; se guardó el resultado de cada promesa, no se ejecutaron con Node. En CSS/JS se desactivó la caché antes de GREEN. No se ejecutó suite Python: no hay cambios Python.
- Consola no capturada de forma fiable. No se afirma ausencia de errores. Captura CDP inicial agotó el tiempo; se obtuvo después con captura de navegador. No se modificó el formato monetario estándar de Intl.

## Diff exacto de producción
```diff
--- static/styles.css
+++ static/styles.css
@@
 .choice > span { line-height: 1.35; }
+#chat-panel label[for^="chat-context-field-"] > span { min-width: 0; overflow-wrap: anywhere; }
--- static/app.js
+++ static/app.js
@@
-  tray.appendChild(textElement("p", help, "small"));
+  tray.appendChild(textElement("p", `${help} La selección y los filtros son temporales y se pierden al recargar la página.`, "small"));
@@
-  ["Escenario", "Estado", "Aportado", "Saldo nominal", "Saldo real"].forEach(label => header.appendChild(el("th", { scope: "col" }, label)));
+  ["Escenario", "Estado", "Horizonte", "Aportado", "Saldo nominal", "Saldo real"].forEach(label => header.appendChild(el("th", { scope: "col" }, label)));
@@
     row.appendChild(el("td", { "data-label": "Estado" }, labels[scenario.status]));
+    row.appendChild(el("td", { "data-label": "Horizonte" }, scenario.form.years ? `${scenario.form.years} años` : "—"));
@@
   table.appendChild(body); tableWrap.appendChild(table); holder.appendChild(tableWrap);
+  if ([state.scenario, state.scenarioSecond].every(s => s.status === "current") && Number(state.scenario.form.years) !== Number(state.scenarioSecond.form.years)) {
+    holder.appendChild(textElement("p", "Los horizontes son distintos: los saldos corresponden a momentos diferentes.", "warning-note"));
+  }
```
La columna refleja el formulario incluso pendiente; solo se muestran importes con estado actualizado. El aviso se aplica cuando ambos resultados están actualizados. La prueba nueva completa está en `prototipos/paideia-local/tests/qa_layout_browser.js`.
