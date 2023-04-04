

class TicketResponse():
    def __init__(self, id, ticket_id, user_id, mensaje, created_at):
        self.id = id
        self.ticket_id = ticket_id
        self.user_id = user_id
        self.mensaje = mensaje
        self.created_at = created_at

    @classmethod
    def from_db(cls, db_row):
        """Construye una instancia de TicketResponse a partir de una fila de base de datos."""
        return cls(*db_row)