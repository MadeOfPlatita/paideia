# B fix1 — política de antigüedad incompleta (offline)

## Resultado y límites
El evaluador cuantitativo exige ambos límites explícitos `timedelta` no negativos. `None` en cualquiera produce `FRESHNESS_BOUNDS_UNCONFIGURED`, `not_comparable`, valores nulos y conserva los demás motivos, incluidos falta de métrica y conflicto. No se asigna ningún TTL; una política íntegramente ausente sigue siendo `FRESHNESS_POLICY_NOT_CONFIGURED` en el servicio. Las identidades sin criterio no pasan por este evaluador. `display` no concede `app_display`. Ningún dato o permiso real se ha activado.

RED: antes del cambio, `python -m unittest discover -s tests -p test_freshness_bounds_offline.py -v` ejecutó 1 test con 3 subtests fallidos, incluyendo un producto de 2020 elegible con `None,None` y ausencia del código para ambos casos parcialmente configurados. GREEN: el mismo comando pasó (4 tests después de añadir fronteras); ver `tests.txt` para ejecución posterior.

## Mapa explícito de migración de tests
- `test_catalogue_facts.CatalogueFactComparabilityTests.test_freshness_policy_is_required_scoped_and_has_no_implicit_ttl`: antes afirmaba que `None,None` permitía comparar fechas sintéticas de octubre de 2026. Se mantiene la prueba positiva con límites explícitos de 24 horas de recuperación y 90 días de efectividad, que cubren esas fechas; se mantienen las comprobaciones de política omitida, límite negativo y ámbito incorrecto. El contrapunto `None,None` ahora se comprueba en `test_each_unconfigured_bound_excludes_and_retains_other_reasons`.
- `test_catalogue_mapping_offline.OfflineMappingTests.test_explicit_unlimited_threshold_policy_currently_allows_old_synthetic_facts` pasa a `test_old_synthetic_facts_require_both_explicit_bounded_thresholds`. Conserva exactamente el contraejemplo de 2020 y la llamada `None,None`, invirtiendo su expectativa a no comparable con valores nulos y motivo estable. Conserva además el resultado positivo con política exclusivamente de prueba de 7×366 días para cubrir el intervalo sintético 2020–2026; no es recomendación ni política productiva.
- Los nuevos tests cubren `None,None`, cada límite por separado, cero como timedelta, números/bool inválidos, frontera exacta y un segundo fuera, fechas futuras, fuente/métrica obsoleta, falta/conflicto y permisos no equivalentes. Los tests existentes de política ausente y comparación de identidades siguen activos.

## Alcance no probado
Pruebas sintéticas y offline no verifican actualidad ni legitimidad de fuentes reales, ni definen umbrales de negocio, publicación, integración remota o capacidades de producción. Los límites de prueba no son TTL aprobados. No se ha probado todo el proyecto; `tests.txt` contiene las suites enfocadas ejecutadas.
