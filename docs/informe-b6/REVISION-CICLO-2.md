# B6 — revisión independiente de la corrección 2

Dictamen recibido 4 de noviembre de 2026: **desfavorable**. Tras dos ciclos de corrección se detiene B6, sin aceptar ni desplegar; no se autoriza un tercer ciclo por cambiar de prueba o revisor.

La revisión confirmó como defectos: discrepancia entre servidor local y WSGI en fichas de productos curados; aviso de comparador que aún afirma que solo se comparan metadatos pese a mostrar tasas; en el ensayo B5, ausencia declarada de condiciones cuando sí hay una condición de snapshot documentada; fechas inválidas que la UI muestra sin validar; y tasas con estado almacenado `known` que la UI puede seguir mostrando como disponibles después de `effective_to`. También detectó estados de carga de fichas engañosos y discrepancias locales/WSGI en validación de entradas de comparación. Los casos de datos corruptos y fecha vencida se reprodujeron mediante inyección controlada de respuestas o snapshots; no prueban que el catálogo real estuviese corrupto.

Se verificaron mejoras en fallo/reintento de biblioteca, fechas en casos normales y el informe con caducidad simulada. El informe descargado revisado no contenía scripts ni perfil; hubo pruebas offline y servidores locales con IA desactivada. No se verificaron Vercel, impresión nativa, impresora ni móvil físico.

El defecto de B5 afecta a la aceptación anterior de ese bloque: Openbank sí se había comprobado, pero ACC-01 demuestra que la cobertura fue incompleta. No presentarlo como aceptado para todos los productos documentados. Evidencia técnica: transcripción `deleg_630fe643`; artefactos temporales del perfil Hermes `cache/scratch/b6-review2-*` y `b6-products-parity.py` (pueden expirar). No se debe destruir ni revertir los cambios locales existentes sin autorización.
