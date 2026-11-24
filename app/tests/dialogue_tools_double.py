"""Dobles de prueba para los turnos con herramientas.

Compartidos por las pruebas del respaldo tras un rechazo: un proveedor que
devuelve un guion de respuestas y graba si le anunciaron herramientas, y dos
despachantes (uno que rechaza y otro que ejecuta y falla).
"""

from __future__ import annotations

TOOLS = [{"type": "function", "function": {
    "name": "search_products",
    "description": "Busca productos del catálogo",
    "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
}}]

_PRODUCTO = {
    "id": "DEP-04", "name": "Depósito Sinycon Plus", "family": "deposito",
    "issuer": "EBN Banco", "primary_url": "https://example.test/x",
    "identity_state": "verified", "publication_ready": False,
    "conditions_state": "documented", "conflicts": [], "unknown_fields": [],
    "conditions": [],
}


class ProveedorGuionizado:
    """Devuelve las respuestas del guion, en orden, y graba las herramientas."""

    test_only = True

    def __init__(self, guion):
        self.guion = list(guion)
        self.llamadas = 0
        self.herramientas = []

    def chat(self, messages, *, tools=None):
        self.llamadas += 1
        self.herramientas.append(tools)
        return self.guion[min(self.llamadas - 1, len(self.guion) - 1)]


class DispatcherQueRechaza:
    """Rechaza la llamada como haría el runner con un nombre no anunciado."""

    def definitions(self):
        return TOOLS

    def dispatch(self, name, arguments):
        return {"schema_version": "local-tools.v1", "tool": name, "status": "error",
                "data": {}, "sources": [],
                "error": {"code": "INVALID_ARGUMENTS", "message": "Los argumentos no cumplen el contrato."}}


class DispatcherQueEjecuta:
    """Ejecuta de verdad (para probar que un fallo tras ejecutar NO se repite)."""

    def __init__(self, falla=False):
        self.falla = falla

    def definitions(self):
        return TOOLS

    def dispatch(self, name, arguments):
        if self.falla:
            return {"schema_version": "local-tools.v1", "tool": name, "status": "error",
                    "data": {}, "sources": [],
                    "error": {"code": "REPOSITORY_ERROR", "message": "No se pudo leer el catálogo."}}
        return {"schema_version": "local-tools.v1", "tool": name, "status": "ok",
                "data": {"items": [_PRODUCTO], "count": 1, "limit": 8},
                "sources": [], "error": None}
