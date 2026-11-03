# B — diagnóstico offline (parcial)

Comando exacto desde `prototipos/paideia-local`: `python -B -m unittest discover -s tests -p 'test_catalogue_mapping_offline.py' -v`. Salida y código en `offline-tests.txt`: 7 pruebas, OK, exit 0. HTTP usa servidor propio loopback efímero, servicio real inyectado, repositorio y hechos exclusivamente sintéticos; cerrado al terminar. No se consultó proveedor externo ni API financiera.

## Contrato observado

- El repositorio usa familia `deposito`; el servicio solo acepta esa familia exacta y construye especificación `term_deposit` / `term_deposit_tae` / `deposit.tae`, `PERCENT`, `EUR`, `12_months`, acción `app_display`. No aplica normalización permisiva. `facts-draft.json` emplea por ejemplo `deposito` / `term_deposit_offer_terms` y permisos `display`; no hay loader de ese draft a `Fact` ni equivalencia automática verificada. `display=allowed` no concede `app_display`; pending/bloqueado también excluye.
- Sin política el servicio devuelve `FRESHNESS_POLICY_NOT_CONFIGURED` y valores null; con política, por defecto excluye los hechos `synthetic_test`. En el fixture autorizado explícitamente para prueba, el DTO positivo indica `test_only`, `not_for_publication` y HTTP `test_only_quantitative`. Los escenarios de familia/scope distintos, permiso, fuente ausente, futuro/caducado y conflicto se cierran; repetición exacta es idempotente.
- No se ha demostrado integración de mapping de draft/schema a hechos, ni navegador; no activar equivalencias sin contrato de derechos y semántica validado. Ninguna prueba establece ofertas, tasas o permisos reales actuales.

## Brecha explícita para coordinación

`FreshnessPolicy(max_retrieval_age=None, max_effective_age=None)` significa expresamente sin límite en la implementación y una prueba preexistente exige que sea comparable. La nueva prueba diagnóstica demuestra que con esa política inyectada y hechos sintéticos antiguos la comparación se habilita. Es distinto de política ausente, que sí cierra. Si el requisito «TTL missing debe cerrar» comprende ambos umbrales `None`, esta conducta requiere decisión y migración coordinada del contrato/tests existentes; no se ha cambiado TTL ni producción ni fingido cierre. No es una reclamación sobre la configuración o datos reales.

No se ha modificado código de producción: las verificaciones del contrato existente pasan inmediatamente, no se reporta un ciclo red→green. El gap de umbrales queda abierto deliberadamente para el coordinador; no se cambian archivos fuera de la propiedad asignada.
