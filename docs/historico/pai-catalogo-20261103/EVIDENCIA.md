# B4 — Pai con catálogo verificado

Fecha: 3/11/2026. Alcance: lectura del catálogo por parte de Pai, aprobada por el equipo.

## Qué se activó

- Nuevo ámbito de herramientas `catalogue_read`. Expone solo `search_products`, `get_product_detail` y `calculate_scenario`. `compare_products` y `get_sources` quedan fuera y el servidor rechaza llamadas a ellas aunque el modelo las pida.
- `catalogue_adapter.py`: vista del catálogo que une los 20 candidatos con los 4 productos transcritos y adjunta las condiciones documentadas (valor, estado, fuente, fecha). La búsqueda ignora acentos y busca por nombre, emisor e identificador.
- La proyección de cada producto se valida campo a campo antes de salir al modelo: métrica, estado (`known`/`stale`/`conflict`/`unknown`), valor decimal en texto, unidad, motivo, fuentes y fecha límite. Cualquier otra forma se descarta.
- El prompt de Pai cambia: ya no dice «no tienes condiciones verificadas», sino que debe consultar el catálogo y citar estado y fuente; sigue prohibido inventar productos, tasas, fuentes o citas.
- Tolerancias del ejecutor de herramientas: se aceptan llamadas sin `family`/`limit`, se normalizan guiones tipográficos en los identificadores y el límite de rondas sube de 2 a 3, porque una comparación necesita búsqueda más dos fichas.

## Llamadas reales verificadas

Servidor local `127.0.0.1:8765`, Groq `openai/gpt-oss-20b`, consentimiento remoto `paideia-chat-remote-v1`.

1. «¿Qué TAE documentada tiene el depósito EBN a 12 meses y cuál es su fuente?»
   - Herramientas: `search_products`, `get_product_detail`.
   - Respuesta: TAE 3,1 % anual, con la URL oficial de EBN Banco.
2. «¿Cuál de estos dos depósitos a 12 meses tiene mejor TAE: el de EBN o el de Self Bank?»
   - Herramientas: `search_products`, `get_product_detail`, `get_product_detail`.
   - Respuesta: EBN 3,1 % frente a Self Bank 2,75 %, y advierte de que la fuente de Self Bank es secundaria (Rankia) y que las cifras pueden cambiar.

## Límites conocidos

- La comparación cuantitativa con criterio (`deposit_tae_12m_eur`) sigue siendo exclusiva del comparador de la aplicación; el chat no puede invocarla.
- La TAE de Self Bank procede de prensa especializada, no de la página oficial; el dato se muestra como documentado pero la respuesta lo señala.
- Groq en plan gratuito devuelve errores intermitentes de proveedor con preguntas largas; la aplicación no reintenta y lo dice.
- El chat solo está encendido en local: la web pública sirve el catálogo y el comparador, sin modelo.
