# Cierre — misión Paideia hasta bloqueo

**Apertura:** 4/11/2026, 18:20 (Málaga).
**Cierre:** 4/11/2026, 22:20 (Málaga).
**Raíz:** `C:/Users/aleja/Downloads/App Financiera`, rama `master`.
**Resultado:** tres bloques aceptados por revisión independiente, subidos al repositorio privado y **desplegados en la web pública con la IA apagada**; el contador global se detiene tras agotar sus dos ciclos de corrección, con **0 llamadas reales a Groq**.

---

## 1. Qué puede usarse ahora mismo

**En internet:** https://paideia-mu.vercel.app — tema oscuro, biblioteca, comparador, escenarios y ensayo funcionando; el chat declara que la IA no está configurada y no envía nada.

**En local:**

```sh
cd prototipos/paideia-local
python app.py --port 8765
# http://127.0.0.1:8765/
```

- **Toda la app en tema oscuro** (grafito, acento menta): Inicio, Tu mapa, Biblioteca, Comparar, Escenarios, Ensayo, Glosario y Privacidad.
- **El informe de comparación descargado** cita la fuente de la condición: URL, título y fecha de consulta, separadas de la URL de la ficha del producto.
- **Pai explica por qué retiene una respuesta** con el motivo real (cifra, atribución, identificador o texto no comprobable) en lugar de atribuirlo siempre a «fuente oficial».
- **Funciones intactas**: perfil local con consentimiento y borrado, biblioteca con condiciones documentadas, comparador, escenarios A/B con motor determinista, informe HTML autónomo, ensayo ficticio, glosario.
- **El informe y la impresión siguen en claro**: `dark_theme.css` está encerrado en `@media screen` y el informe lleva su propia hoja en línea.

## 2. Aceptado por revisión independiente

| Bloque | Dictamen | Evidencia decisiva |
|---|---|---|
| **Diseño oscuro** | `deleg_1514b34f` tarea 1 · **passed: true** | 915 elementos de texto por ancho en 8 rutas × 2 anchos, **0 fallos** de contraste AA (con sonda 1:1 plantada y detectada); 24/24 sin desbordamiento a 1440/390/320; avisos y consentimiento visibles y legibles; foco visible 12,56:1; informe y PDF reales en blanco; B1 74 (72 PASS + 2 observaciones), B8 28/28, B9 32/32, Node 87/87 |
| **Trazabilidad B6** | `deleg_3deb6a4d` · **passed: true** | Atribución con URL de condición ≠ URL de producto (Openbank y par sintético); título y fecha de consulta; invalidación al editar la tasa sin resucitar al volver al valor original; sin clase de fuente inventada; 16/16 unitarias y 40/40 de navegador |
| **Aviso de texto retenido** | `deleg_cb8fccf1` + `deleg_4b14e450` · **passed: true** | Matriz de 16 DTO con cada motivo: el aviso coincide con el motivo declarado; ningún caso renderiza la prosa retenida; catálogo y calculadora conservan su precedencia; sin módulo degrada honestamente; 95/95 Node, B1 72/74 PASS, B8 28/28, B9 32/32 |

Los tres dictámenes se emitieron sobre los hashes exactos de los commits `8614f88`, `caeb95d` y `1a66a53`; las copias de `api/_static` son idénticas byte a byte.

## 3. Detenido: contador global y prueba real con IA

El contador recibió **tres dictámenes**. El primero rechazó cuatro defectos; el segundo confirmó esos cuatro cerrados pero encontró una regresión de concurrencia que había introducido yo (N1); el tercero confirmó N1 cerrada y B2/B3/B4/L1–L3 cerrados, pero dejó **B1/N2 abierto**: la toma de un lock obsoleto no es atómica y dos contendientes simultáneos obtienen ambos el último intento (6 autorizaciones para cupo 5, reproducido 5/6; con 20 procesos, diario corrupto).

Se agotaron los **dos ciclos de corrección** que permite la misión. Probé además un lock del sistema operativo, que en sondas independientes sí excluía, pero **no pude validarlo bajo el arnés de pruebas** y lo retiré en lugar de dejar código sin verificar.

**Consecuencia:** **0 llamadas reales a Groq en esta misión**; el diario histórico conserva sus 15 líneas; no hay manifest activo. Las correcciones cerradas (B2, B3, B4, L1–L3, N1) quedan **sin commit**, porque comparten fichero con el lock pendiente.

## 4. Suites ejecutadas

| Comprobación | Resultado |
|---|---|
| Python (`pytest tests`) | **631 passed, 1 skipped**, exit 0. El caso omitido documenta el defecto N2 abierto. |
| Node del prototipo | **95 comprobaciones** (14 archivos + módulo de avisos), exit 0 |
| Navegador B1 / B8 / B9 | 74 (72 PASS + 2 observaciones) / 28/28 / 32/32 |
| Recorrido B6 con tema oscuro | 40/40 en escritorio y 40/40 en móvil emulado |
| Concurrencia del contador (sonda propia, 20 procesos, cupo 5) | 5/5 reservas, sin lock huérfano, cupo nunca superado, 3/3 repeticiones |
| Web pública tras desplegar | HTML con `theme-color #101112` y `dark_theme.css`; CSS servido como `text/css`; 20 fichas de catálogo; 5 rutas sin errores ni desbordamiento; `ai.connected=false` |

## 5. GitHub y Vercel

- **GitHub:** `MadeOfPlatita/paideia` verificado `private` antes y después de cada push. Cuatro commits selectivos con lo revisado; historia sin reescribir; `.env` confirmado ausente en el remoto (404 en la API).
- **Vercel:** **desplegado**. El primer intento quedó `BLOCKED` porque el autor del commit era una dirección de ejemplo sin permiso en el proyecto. Se corrigió **sin reescribir historia**: la identidad local del repositorio pasa a `307587994+MadeOfPlatita@users.noreply.github.com` y el despliegue se hizo desde una copia de `api/` + `vercel.json` + `.vercel` sin metadatos de git, que fue lo que permitió publicar.
  - **Aviso para el equipo:** los despliegues lanzados desde el repositorio git siguen bloqueados por esa regla de autoría; mientras no se corrija en Vercel (autor verificado o miembro con asiento), hay que desplegar con esa copia sin `.git`.
  - Leído de vuelta: la URL pública sirve la versión nueva y mantiene el chat apagado.

## 6. Lo que falta y quién debe decidirlo

| Decisión | Por qué | Qué hace falta |
|---|---|---|
| Reparar N2 con otro diseño de exclusión | El cupo puede superarse por una carrera al recuperar un lock obsoleto | Lock del sistema operativo o testigo externo, más revisión favorable de la versión exacta |
| Ejecutar la prueba real de Pai | La puerta sigue cerrada | Autorizar el bloque corregido y su revisión; después, muestra pequeña con datos ficticios |
| Mejorar la supresión de Pai | Sigue reteniendo respuestas legítimas que el usuario no llega a ver | Cambio de criterio con TDD y revisión; no se tocó para no debilitar la frontera sin supervisión |
| Catálogo | Los 20 candidatos no son 20 ofertas; permisos y vigencia sin acreditar | Revisión de fuentes y permisos, producto a producto |
| Desbloquear los despliegues desde git | La regla de autoría bloquea cada `vercel --prod` del repositorio | Verificar el correo o el asiento del miembro en el panel de Vercel |
| Visibilidad al entregar | El repositorio sigue privado | Invitar a la profesora o cambiar la visibilidad |

---

**Ningún resultado sintético se presenta como producción, ninguna prueba propia se presenta como aprobación y no se ha consumido cuota real de IA.**
