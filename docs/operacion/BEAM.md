# Beam 1.0 en Paideia: estado al 5/11/2026

## Lo que ya está hecho y desplegado

- `app/providers.py` tiene tres destinos anclados: Groq (`api.groq.com`),
  Command Code (`api.commandcode.ai`) y Vercel AI Gateway (`ai-gateway.vercel.sh`).
  La clave de un proveedor no puede viajar al host de otro.
- El modelo por defecto de **Command Code** es `reflection/beam:free`, que es el
  Beam 1.0 gratuito que aparece en el plan del usuario con 0 % de uso.
- El tope de espera sube de 20 s a **60 s** en el transporte y en `pai_setup.py`:
  Beam razona antes de escribir y con 20 s se cortaba.
- El estado público dice con qué proveedor está configurado el chat
  (`ai.provider`) y, si el proveedor rechaza la credencial, el mensaje incluye el
  código HTTP real.
- Suites: **701 Python + 108 Node** en verde. El caso de puerto ocupado
  (`test_failed_start_is_terminal_and_explains_occupied_port`) falla solo cuando
  otro proceso tiene el puerto; aislado pasa.

## Lo que bloquea a Beam ahora mismo

Dos caminos, los dos con un paso manual en un panel web:

1. **Vercel AI Gateway** (`PAIDEIA_LLM_PROVIDER=vercel`), que es lo que hay
   configurado. El servicio responde `HTTP 401`: la clave guardada en Render no
   es válida. Para crear una nueva, Vercel pide un código de 6 dígitos por correo,
   así que no se puede automatizar sin acceso al buzón. El modelo por defecto de
   esta ruta es `reflection/beam-free` (con guion).
2. **Command Code** (`PAIDEIA_LLM_PROVIDER=commandcode`), que ya tiene clave
   válida en Render y ya contestó preguntas reales. Solo falta cambiar esa
   variable: con ella, el chat usa `reflection/beam:free` y el tope de 60 s.

## Pasos exactos para dejarlo en Beam

Render → `paideia` → Environment → `Edit`:

1. En la fila `PAIDEIA_LLM_PROVIDER`, cambiar `vercel` por `commandcode`.
2. `Save, rebuild, and deploy`.

No hace falta tocar claves. Después:

```bash
curl -s https://paideia-jg2n.onrender.com/api/status | python -m json.tool
```

Debe decir `"provider": "Command Code"`. La primera pregunta real puede tardar
hasta un minuto: Beam piensa antes de responder.

## Por qué no lo cambió el asistente

Render pinta la tabla de variables con virtualización: el árbol de accesibilidad
solo expone **una** fila a la vez y no publica los nombres, así que no hay forma
de distinguir `PAIDEIA_LLM_PROVIDER` de `GROQ_API_KEY` sin arriesgar renombrar o
borrar una clave. Escribir a ciegas ahí podía dejar el servicio sin credenciales,
y se prefirió no hacerlo.

## Si Beam no responde por Command Code

El plan lo lista, pero el endpoint puede no servirlo. En ese caso la vuelta atrás
es inmediata: poner `PAIDEIA_LLM_PROVIDER=commandcode` con
`PAIDEIA_LLM_MODEL=deepseek/deepseek-v4.1-flash` (ya probado), o volver a
`groq` con `PAIDEIA_GROQ_MODEL=openai/gpt-oss-120b`. Ninguna de las dos requiere
tocar código.
