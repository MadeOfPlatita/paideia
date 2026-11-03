# Regresión del aviso de privacidad — 30-10-2026

## Alcance y causa

Datos y captura sintéticos. En el autoguardado, `ok:false` también indicaba limpieza de claves antiguas incompleta tras escribir la instantánea; `recordProfileAnswer` lo trataba como escritura fallida y el aviso global ocultaba `storageNotice`. Ahora se distingue `snapshotWritten` de fallo de escritura; se muestran por separado el aviso de cambios potencialmente no guardados y el estado de las copias, y se permite reintentar cuando el perfil está activado. Al recargar se informa específicamente de residuos antiguos detectados. La eliminación puede ser incompleta o no comprobable; el texto no asegura su borrado.

## Evidencia

- RED de `tests/profile_autosave_residue_ui.js`: con `setItem` correcto y `removeItem` de clave antigua arrojando excepción, se guardó la instantánea nueva pero se mostró «la copia guardada podría ser una versión anterior... puedes perder esos cambios» y no se informaba de residuos.
- GREEN: sobre navegador de prueba aislado y `python -m http.server 18789 --bind 127.0.0.1 --directory static`, el mismo fixture verificó instantánea nueva, residuo, aviso en el viewport, navegación a Biblioteca, fallo de reintento manteniendo el aviso, recarga real, recuperación del valor ficticio 123 y reintento exitoso que eliminó el residuo y retiró el aviso. Quedaron `localStorage` y `sessionStorage` vacíos. Ver `aviso-residuos-sintetico.png`; el servidor estático carece de API y por ello el estado de servicio aparece sin respuesta (404 esperados de `/api/status` y `/api/catalogue`).
- Navegador: pasaron secuencias anteriores `profile_autosave_failure_ui.js` → recarga → `profile_autosave_retry_ui.js`, `profile_autosave_ui.js` → recarga → mismo fixture, `profile_partial_ui.js` → recarga → `profile_partial_delete_ui.js` → recarga → `profile_partial_retry_ui.js`, y `profile_help_optin_ui.js`. Se comprobaron copia previa tras fallo de escritura, reintento, aviso antes de opt-in, persistencia, borrado parcial y limpieza final.
- `node --test tests/*.test.cjs`: 39/39 aprobadas. `node --check static/app.js` y `node --check static/profile_model.js`: correctos. El test Node añadido verifica instantánea 123, residuo tras recarga y limpieza comprobada en reintento; los tests previos cubren eliminación silenciosa y lectura no verificable.
- Servidor de prueba terminado; `netstat` no muestra LISTENING en 18789 (solo conexiones TIME_WAIT) y `curl` no conecta. Navegador de prueba vaciado.

No se probaron credenciales, API real, backend completo, datos personales ni despliegue. Esta corrección requiere revisión independiente y no implica aprobación de privacidad general ni del resto del proyecto. No existe repositorio Git acreditado en esta carpeta; no hay diff Git.
