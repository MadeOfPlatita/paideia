# Privacidad del almacenamiento del perfil — 30-10-2026

## Alcance y comportamiento

El guardado sigue exigiendo opt-in explícito. Si se escribe la instantánea actual pero falla o no se puede verificar la eliminación de claves antiguas, se informa de la escritura y de posibles copias residuales; no se intenta un rollback. La recarga detecta una clave antigua residual o una lectura no verificable junto a una instantánea válida. Al borrar, se intentan todas las claves actuales y anteriores y se leen de nuevo; solo se anuncia borrado completo si ninguna operación falló y todas las lecturas confirman ausencia. Una excepción de escritura/lectura o un borrado parcial producen un estado incompleto o desconocido, no «solo memoria». La revocación desactiva el guardado en la pestaña incluso si falla el borrado; se puede reintentar.

**Límite:** si la copia actual sobrevive al borrado fallido, una recarga puede recuperarla y restaurar el opt-in anterior, porque no se ha podido borrar y no se introduce un marcador persistente que pudiera también fallar. La interfaz vuelve a indicar que existe una copia. El usuario debe reintentar el borrado o gestionar los datos del sitio en el navegador. La comprobación cubre únicamente las claves soportadas y el instante de lectura; no es garantía frente a otras pestañas, extensiones, restauraciones o almacenamiento fuera de esas claves. No hay consentimiento para tratamiento remoto derivado del opt-in local.

## Evidencia TDD

Desde `app`:

- `node --test tests/profile_partial_storage.test.cjs`: RED inicial, `snapshotWritten` ausente en la escritura exitosa con `removeItem` fallido; GREEN tras el cambio.
- Mismo comando: RED para borrado que no elimina y lectura posterior que falla (`true !== false`); GREEN después de verificar claves.
- Mismo comando: RED para residuo antiguo al recargar (`null` frente a `legacy_residue`); GREEN con detección.
- Mismo comando: RED para limpieza antigua que no elimina pese a no lanzar; GREEN con verificación.
- `node --test tests/*.test.cjs`: 38 pruebas, 38 aprobadas.
- UI RED real: `tests/profile_partial_ui.js` sobre página loopback mostró «No se pudo guardar. El mapa sigue solo en memoria» y «Ahora: solo memoria de esta pestaña», aun existiendo instantánea; GREEN mostró guardado y advertencia de copias anteriores.

## Reproducción navegador loopback

Sin instalación, secretos ni backend IA: iniciar desde la raíz de app `python -m http.server 18765 --bind 127.0.0.1 --directory static`. Abrir `http://127.0.0.1:18765/#perfil` en un navegador de prueba aislado, limpiar localStorage de ese origen y recargar. Evaluar el contenido de `tests/profile_partial_ui.js`; recargar; evaluar `tests/profile_partial_delete_ui.js`; recargar; evaluar `tests/profile_partial_retry_ui.js`; recargar y comprobar `localStorage.length === 0`. Las pruebas usan perfil ficticio, cero declarado y fallos sintéticos en `Storage.prototype.removeItem`; no deben ejecutarse sobre un origen con datos reales. Resultado real: guardado parcial advertido; recarga conservó opt-in y cero; fallo de borrado dejó copia y mostró advertencia; recarga recuperó la copia superviviente; reintento retiró claves y la última recarga mostró memoria y cero claves. Restaurar los prototipos y cerrar el servidor al terminar.

La revisión independiente queda pendiente. No se modificó el backend Groq ni se llamó a servicios externos; no se prueba seguridad general, concurrencia entre pestañas ni conservación/borrado fuera de las claves propias.

## Revisión: aviso de guardado automático

La revisión independiente detectó que el aviso anterior prometía escritura solo al pulsar Guardar, pero, tras el opt-in y el primer guardado, las respuestas posteriores se guardan automáticamente. Se conserva ese comportamiento autorizado: el texto previo al opt-in y la confirmación de guardado informan ahora de los cambios posteriores en este navegador y aclaran que no se autoriza envío remoto. No se cambió el diseño ni el backend.

**TDD UI real:** `tests/profile_autosave_ui.js`, ejecutado en navegador aislado contra el servidor estático loopback: RED tras guardar, editar sin volver a pulsar Guardar y recargar; el valor ficticio 123,00 persistió, pero faltaba el aviso previo. GREEN tras corregir los textos: se verificaron aviso previo, confirmación, persistencia tras recarga y almacenamiento vacío al terminar. El primer guardado requiere casilla y botón; la prueba comprueba que ni el cuestionario previo ni marcar la casilla escriben por sí solos. Para reproducir, iniciar el servidor del apartado anterior, abrir el origen aislado limpio, evaluar el fixture, recargar efectivamente y volver a evaluarlo; cerrar el servidor. No ejecutarlo sobre datos reales: limpia los almacenamientos de ese origen al finalizar.

`node --test tests/*.test.cjs`: 38 pruebas, 38 aprobadas. Limitaciones de aquella prueba: el fixture UI no formaba parte de la suite Node y no validaba envío remoto ni condiciones de fallo de almacenamiento, concurrencia o seguridad general.

## Segundo y último ciclo de corrección

- Ayuda contextual: RED `tests/profile_help_optin_ui.js` en navegador loopback aislado: después de autorizar y guardar afirmaba «solo queda en memoria». GREEN: indica que se intentan guardar automáticamente los cambios en el navegador y que el permiso no autoriza envío remoto. Sin opt-in distingue memoria actual de almacenamiento cuyo estado sea desconocido.
- Autoguardado: RED `tests/profile_autosave_failure_ui.js`: con copia ficticia que contiene cero y `setItem` fallando, el resumen mostraba 123 pero no aparecía aviso inmediato. GREEN: aviso global con `role=alert`, diferencia memoria de copia potencialmente anterior, advierte pérdida al recargar y ofrece reintentar. Persiste entre pantallas y ante reintento fallido; solo se retira tras guardado confirmado o borrado completo verificado. El almacenamiento ilegible al inicio también se advierte globalmente.
- `profile_autosave_retry_ui.js`, tras una recarga real desde el fallo: se recuperó el cero antiguo, no 123; se reprodujo otra vez el fallo, se mantuvo el aviso tras interacción y un reintento fallido, y el reintento exitoso guardó 123, comprobado con nueva recarga. Revocar borró las claves y la recarga final dejó cero claves. Tras recargar se pierde el estado en memoria y no puede garantizarse un aviso retrospectivo del cambio perdido si no pudo persistirse: la advertencia es anterior a la recarga.
- Regresión de guardado y borrado parcial: `profile_partial_ui.js`, recarga, `profile_partial_delete_ui.js`, recarga, `profile_partial_retry_ui.js`, recarga: pasó; el cero declarado sobrevivió al borrado fallido, el reintento verificó eliminación y quedaron cero claves. Lectura inaccesible simulada antes de cargar mantuvo aviso al navegar a Biblioteca. `node --test tests/*.test.cjs`: 38/38 aprobadas.
- Tráfico observado: servidor fixture `tests/serve_d_fixture.py` ligado a 127.0.0.1 con perfil ficticio, puerto efímero y navegador de prueba. Antes de las cargas se instrumentaron `fetch` y `XMLHttpRequest` con un script CDP que registra URL/cuerpo y bloquea destinos fuera del origen; además se inspeccionaron entradas Resource Timing. En las rutas ejercitadas se observaron GET locales sin cuerpo a `/api/status` y, al abrir Biblioteca, `/api/catalogue`; recursos observados del mismo origen. No se observaron valores de perfil en esas peticiones capturadas. Esto no prueba ausencia universal de tráfico ni cubre todos los mecanismos, pestañas o rutas; no se ejercitó chat ni proveedor. Sin credenciales, datos reales, instalación ni backend modificado.

Para repetir: iniciar `python tests/serve_d_fixture.py`, utilizar exclusivamente el puerto loopback impreso y un origen aislado sin datos reales; limpiar su almacenamiento y recargar. Evaluar el fixture de ayuda; limpiar y recargar; evaluar el de fallo, recargar realmente, evaluar el de reintento, recargar y comprobar 123, revocar y comprobar cero claves tras otra recarga. Para el borrado parcial usar la secuencia anterior. Inyectar instrumentación de red antes de cargar y conservar sus registros; cerrar el servidor. Los fixtures UI no pertenecen a la suite Node. Revisión independiente de este segundo ciclo pendiente.
