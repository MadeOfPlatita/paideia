# Preparación de regresión sin Tk

`test_session_ui_feedback.py` menciona `tkinter`; `test_mission_session.py` menciona `mainloop`. Por prudencia se excluirán ambos módulos de la regresión de Python de esta misión y se parcheará `tkinter.Tk` para impedir creación de ventanas nativas durante los demás tests. Esto no acredita la suite Python completa: el informe debe indicar módulos excluidos y número real de pruebas ejecutadas.

Coordinador ejecutó `node --test tests/*.test.cjs`: 38 pruebas aprobadas, 0 fallidas, tras los cambios de privacidad. Hora de inicio registrada por `date`: 2026-10-30T12:05:27+01:00. Pendiente revisión independiente.
