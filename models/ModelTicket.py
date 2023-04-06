from .entities.Ticket import Ticket

class ModelTicket():
    
    @classmethod
    def get_tickets_by_user(self, db, current_user_id):
        try:
            cursor = db.connection.cursor()
            sql = """SELECT id_ticket, departamento, numero_contacto, descripcion,
                    estado, created_at from tickets WHERE user_id = '{}' """.format(current_user_id)
            cursor.execute(sql)
            row = cursor.fetchall()
            if row != None:
                ticket_by_user = Ticket(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
                return ticket_by_user
        except Exception as ex:
            raise Exception(ex)