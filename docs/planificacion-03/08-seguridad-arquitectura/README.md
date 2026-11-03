# Seguridad y arquitectura de Paideia

> **Integración posterior:** leer primero `../19-integracion/CRITERIO-INTEGRACION.md`. La allowlist de dos tools y la limitación del perfil local de C09 son propuestas históricas superadas por ese criterio: cinco tools de lectura/cálculo con gates, perfil financiero local y proyección remota seleccionada. No se han activado ni probado. Los schemas y fixtures de este frente requieren adaptación antes de una integración.

Paquete de diseño, no evidencia de implementación ni de prueba. Leer en este orden:

1. [`threatmodel.md`](./threatmodel.md): alcance, fronteras, amenazas priorizadas y decisiones abiertas.
2. [`controles.json`](./controles.json): controles con propósito, aceptación, evidencia requerida, prioridad y estado.
3. [`contratos-error.md`](./contratos-error.md): estados/respuestas seguros y política de reintentos.
4. [`checklist-bloqueos-antes-publicar.md`](./checklist-bloqueos-antes-publicar.md): puertas de salida (pendiente equivale a no publicar esa capacidad).
5. [`fixtures/seguridad-inerte.json`](./fixtures/seguridad-inerte.json): fixtures sintéticas que no deben ejecutarse ni conectarse a red/proveedor.

El chat externo y la ingesta permanecen apagados hasta satisfacer los prerrequisitos y pruebas de aceptación en staging propio. No se realizaron pruebas de seguridad, carga ni llamadas de proveedor.