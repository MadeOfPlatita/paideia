# Cupo de llamadas: qué protege y qué no

## Qué hay hoy

La app cuenta las llamadas **en memoria del proceso** (`pai_setup.py`,
`AdmissionPolicy`): 10 por minuto y 300 al día por defecto, configurables con
`PAIDEIA_CALLS_PER_MINUTE` y `PAIDEIA_CALLS_PER_DAY` (topes 60 y 5000).

Ese contador **se reinicia** cuando:

- Render redespliega (cada push a `master`).
- El servicio se reinicia o se despierta tras dormir 15 minutos.
- Se levanta otra instancia (Render puede tener más de una).

Por eso el número que muestra la app es «llamadas de este proceso», no una cuota
diaria global. Sirve para lo que fue pensado: cortar un bucle, un reintento o
una persona pulsando enviar en cadena. No sirve como presupuesto contable.

## Qué límites sí son reales

1. **Proveedor:** el plan gratuito de Groq aplica sus propios límites por minuto
   y por día; el que manda es el suyo, y la app lo traduce a un aviso de límite
   temporal (429) sin reintentar sola.
2. **Tamaño:** entrada acotada (16 KB de petición), salida máxima de 900 tokens y
   un turno como máximo en vuelo por proceso (`max_concurrent=1`).
3. **Ritmo:** 10 peticiones por minuto por proceso, que ya limita un abuso
   trivial desde el enlace público.

## Qué haría falta para una cuota diaria de verdad

Un almacén compartido fuera del proceso (Redis/Upstash o una base de datos) con
una clave de servicio. Implica crear una cuenta, guardar una credencial y añadir
dependencia en el arranque; ninguna de las tres cosas cabe en el plan gratuito
sin una decisión del equipo.

Mientras no exista, el límite honesto es: **300 llamadas por proceso y 10 por
minuto**, más los límites del proveedor. La app lo dice así en el panel de Pai.

## Cuando el servicio duerme

El plan gratuito de Render suspende la instancia tras 15 minutos sin tráfico. Al
volver, el proceso arranca de cero: el contador también. El primer acceso puede
tardar alrededor de un minuto.

## Si se quiere cerrar el acceso

Con el enlace público cualquiera puede consumir esas llamadas. Si hiciera falta,
lo razonable es poner una contraseña delante (una variable de entorno y una
comprobación) o limitar por IP en el proxy; ambas cosas son cambios pequeños,
pero son una decisión de producto.
