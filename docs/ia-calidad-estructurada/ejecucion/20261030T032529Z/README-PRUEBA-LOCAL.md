# Prueba local de la modalidad estructurada

Solo para ensayos con datos ficticios. No necesita clave, proveedor externo ni instalación. Desde `C:/Users/aleja/Downloads/App Financiera/prototipos/paideia-local`, ejecutar en una terminal:

```bash
python -B -u tests/serve_structured_fixture.py --port 8771
```

La ejecución usada para esta evidencia mostró `STRUCTURED_FIXTURE test_only=True port=8771`. Abrir `http://127.0.0.1:8771/#inicio`; escribir únicamente `SYNTHETIC TEST ONLY: explain`, aceptar el aviso y enviar. Los textos son editoriales de Paideia, servidos por un proveedor de selección ficticio: no son una respuesta de Groq. Otros casos: para `SYNTHETIC TEST ONLY: calculate`, marca «Añadir escenario ficticio» e introduce explícitamente capital `1000`, tasa `3`, años `1`, aportación `0`, inflación `0` y método `simple`; el motor devuelve `1030.00`. `SYNTHETIC TEST ONLY: forged` provoca un error de contrato sin mostrar el texto de prueba.

Para detenerlo, usar Ctrl+C en esa terminal. El coordinador detuvo su proceso propio mediante el gestor de procesos y deberá comprobar puerto cerrado al finalizar. El fixture solo escucha en 127.0.0.1, no es hosting ni producción.
