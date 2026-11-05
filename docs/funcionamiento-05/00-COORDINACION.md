# Funcionamiento 05 — coordinación

## Encargo y decisión pendiente

El grupo está de acuerdo con las prioridades funcionales y pide trabajar en paralelo. Cuestiona que sea necesario PostgreSQL al usar APIs. No se interpreta como autorización para crear ni eliminar una DB, crear cuentas, instalar, pagar, desplegar o enviar datos reales. Se comprobará si un repositorio/caché normalizado y persistente basta para este proyecto. Las APIs son fuentes; almacenamiento y tolerancia a fallos son decisiones independientes.

Contrato previo a los despachos: [00-CONTRATO.md](00-CONTRATO.md). Lote real: `deleg_09c6c535`, siete agentes. El coordinador conserva integración HTTP/servicios y la verificación final. Las siete entregas se recibieron, revisaron y reprodujeron. Herramientas/orquestación/admisión se conectaron a la frontera HTTP y el perfil se probó en navegador real. Ver 08-integracion/REVISION-COORDINADOR.md y VERIFICACION.json: 155 tests Python, 13 Node, 19/19 HTTP y 16 combinaciones ruta/tamaño. IA real, datos comparables y hosting de producción siguen pendientes; no se ha creado DB ni desplegado.

| Frente | Agente | Salidas exclusivas | Criterio para recibir |
|---|---|---|---|
| 1. Almacenamiento sin DB obligatoria | sa-0-6a8357d5 | 01-almacenamiento/ y spikes/005-api-cache-vs-direct/ | Prueba propia de APIs fake directas vs caché persistente, fallo/reinicio/concurrencia; recomendación condicionada, no nube probada |
| 2. Cinco herramientas de Pai | sa-1-224d1b13 | pai_tools.py, test_pai_tools.py, PAI-TOOLS.md, 02-tools/ | Contrato local-tools.v1, fuentes/IDs/cálculos exactos, entradas cerradas y tests offline |
| 3. Perfil completo funcional | sa-2-dcb682de | app.js, index.html solo montaje, profile_model.js, profile_model.test.cjs, PERFIL-FUNCIONAL.md, 03-perfil/ | Flujo navegable sin diseño nuevo, estados/edición/migración/opt-in/borrado y ausencia de envío del perfil |
| 4. Condiciones de productos reales | sa-3-7eb83d2d | 04-datos-reales/ | Hechos/brechas por los veinte candidatos, fuente/fecha/permiso/conflicto; cero valores inventados o publicación automática |
| 5. Modelo ↔ herramientas | sa-4-b3d18231 | pai_runtime.py, test_pai_runtime.py, PAI-RUNTIME.md, 05-orquestacion/ | Ciclo acotado con proveedor test-only y constructor real de requests, límites/citas/errores y sin razonamiento expuesto |
| 6. Admisión/cupo/cola | sa-5-4d6e4aff | chat_admission.py, test_chat_admission.py, ADMISION-CHAT.md, 06-admision/ | Invariantes con cien solicitudes sintéticas, cuota explícita y límites de persistencia/réplicas honestos |
| 7. Alojamiento gratuito | sa-6-04ab7e7a | 07-alojamiento/ | Hasta tres opciones y ocho páginas primarias, runtime/persistencia/cuotas/tarjeta/suspensión; recomendación, no despliegue |

Las rutas de código son relativas a app/ (tests bajo tests/, frontend bajo static/). Las rutas de informe son relativas a esta carpeta. Nadie modifica CSS. Los siete agentes tienen las mismas fronteras de permisos y salidas exclusivas.

## Dependencias y recepción

1. Reproducir los tests de herramientas y orquestación y comprobar sus contratos entre sí antes de conectarlos a LocalChatService.
2. Probar la ampliación del perfil en navegador limpio sin consultar datos reales del navegador del equipo. Repetir rutas existentes.
3. No cargar facts-draft como ofertas sin revisar evidencia y derechos. Revisar por acción, no inferir licencia por 200/URL/ISIN.
4. Reconciliar persistencia/caché con el runtime gratuito elegido, incluidos límites de reinicio y réplicas para cuotas. Una cola local no prueba 100 conversaciones reales.
5. Verificar API/recorrido completo tras integrar y actualizar estado, diario y evidencias. Los tests aislados no cierran el producto.
6. IA real y A/B/C siguen pendientes de acceso gratuito y configuración segura autorizados. No pedir ni pegar claves en chat.

## Corrección comunicada al agente de admisión

No afirmar que un contador en memoria impide resetear presupuesto al reiniciar. Exigir estado restaurado/inyección explícita o documentar límite y fallo cerrado ante estado desconocido; sin DB ni coordinación de réplicas inventadas.
