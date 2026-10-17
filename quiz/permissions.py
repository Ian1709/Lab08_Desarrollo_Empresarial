from rest_framework.permissions import SAFE_METHODS, BasePermission

AGENT_GROUP = 'agente'

# Métodos de escritura que el agente SÍ puede usar (crear y modificar).
AGENT_WRITES = ('POST', 'PUT', 'PATCH')


class AgentPermission(BasePermission):
    """Quién puede hacer qué. Esta es la regla del SERVIDOR: se aplica aunque un
    cliente se comporte mal, porque vive detrás de cada petición.

    La regla que pide el laboratorio:
      - una persona (usuario con is_staff) puede todo;
      - un miembro del grupo «agente» puede leer, crear y modificar, pero NUNCA
        borrar;
      - cualquier otro usuario autenticado solo puede leer;
      - un método desconocido se deniega (denegar por defecto).

    Sin token, la comprobación llega aquí con ``request.user`` anónimo: se
    deniega (aunque IsAuthenticated ya habría respondido 401 antes).
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False  # denegar por defecto

        # La persona (staff) puede todo.
        if user.is_staff:
            return True

        # El agente: leer, crear y modificar; nunca borrar.
        if user.groups.filter(name=AGENT_GROUP).exists():
            return (
                request.method in SAFE_METHODS
                or request.method in AGENT_WRITES
            )

        # Cualquier otro usuario autenticado: solo lectura.
        return request.method in SAFE_METHODS
