

class Ticket():
    def __init__(self, id_ticket, user_id, user_fullname, departamento, tipo_problema, descripcion, status, created_at):
        self.id_ticket = id_ticket
        self.user_id = user_id
        self.user_fullname = user_fullname
        self.departamento = departamento
        self.tipo_problema = tipo_problema
        self.descripcion = descripcion
        self.status = status
        self.created_at = created_at

    @classmethod
    def from_db(cls, db_row):
        """Construye una instancia de Ticket a partir de una fila de base de datos."""
        return cls(*db_row)