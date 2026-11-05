# Revisión independiente 1: no aprobada

Fuente: deleg_77875590. Alcance: archivos actuales; sin repositorio Git. Pruebas focalizadas: 9 Python,33 subtests y3 Node aprobados, lo que no evitó detectar fallos de límites de confianza.

1. **Seguridad — supuestos del cálculo:** el proveedor elegía los parámetros sin estar vinculados a datos expresos del turno. El motor sí se ejecutaba, pero `deterministic_local` no demostraba que el escenario respondiera a la intención del usuario.
2. **Seguridad — fallback:** el frontend consultaba capacidad mutable al recibir respuesta. Un cambio de estado y DTO ausente podían producir salida como texto legado.
3. **Lógica — DTO en interfaz:** el validador aceptaba IDs/textos arbitrarios, duplicados y `calculation.data` sin validar de forma exhaustiva; esto requiere respuesta HTTP adulterada o fallo del backend, no se demostró penetración a través del proveedor bajo implementación previa.
4. **Legado:** el filtro léxico conserva el fallo documentado y el camino legacy es ejecutable; no se considera corregido ni se autoriza su uso productivo. Las aserciones nuevas estructuradas no son prueba de seguridad del legado.

Se ha iniciado ciclo de corrección1 de máximo2, con archivos exclusivos para backend y frontend. El nuevo contrato vinculará los parámetros explícitos del mismo request; no afirmará que interpretar automáticamente texto libre equivale a consentimiento. Las evidencias anteriores son provisionales y no constituyen aprobación final.
