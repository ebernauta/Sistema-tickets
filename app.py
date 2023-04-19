from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_mysqldb import MySQL
from flask_wtf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
from config import config
import json
from collections import defaultdict
import matplotlib.pyplot as plt
# Models:
from models.ModelUser import ModelUser
from models.ModelTicket import ModelTicket 


# Entities:
from models.entities.User import User
from models.entities.Ticket import Ticket


app = Flask(__name__)
csrf = CSRFProtect(app)
db = MySQL(app)
login_manager_app = LoginManager(app)


@login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(db, id)

@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User(0, request.form['user'], request.form['password'])
        logged_user = ModelUser.login(db, user)
        if logged_user != None:
            if request.form['user'] == "admin":
                if logged_user.password:
                    login_user(logged_user)
                    return redirect(url_for('panelAdmin'))
                else:
                    flash("Contraseña incorrecta...", 'danger')
                    return render_template('auth/login.html')
            else:
                if logged_user.password:
                    login_user(logged_user)
                    return redirect(url_for('home'))
                else:
                    flash("Contraseña incorrecta...", 'danger')
                    return render_template('auth/login.html')
        else:
            flash("Usuario no encontrado...", "danger")
            return render_template('auth/login.html')
    else:
        return render_template('auth/login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/generarTicket', methods=['GET', 'POST'])
@login_required
def generarTicket():
    if request.method == 'POST':
        cursor = db.connection.cursor()
        user_id = current_user.id
        user_fullname = current_user.fullname
        departamento = request.form['departamento']
        numeroContacto = request.form['numeroContacto']
        descripcion = request.form['descripcion']
        status = 'Pendiente'
        tipo_problema = ''
        create_at = datetime.now()
        sql = """ INSERT INTO tickets (user_id, user_fullname, departamento, numero_contacto,
                    descripcion, estado, created_at, tipo_problema) VALUES 
                    ('{}','{}','{}','{}','{}','{}', '{}', '{}')""".format(user_id, user_fullname ,departamento, numeroContacto,
                                                            descripcion, status, create_at, tipo_problema)
        cursor.execute(sql)
        return redirect(url_for('home'))

@app.route('/mis-tickets')
@login_required
def home():
    cursor = db.connection.cursor()
    sql = """SELECT id_ticket, user_fullname, departamento, numero_contacto, descripcion,
                estado, created_at FROM tickets WHERE user_id = '{}' ORDER BY created_at DESC""".format(current_user.id)
    cursor.execute(sql)
    row = cursor.fetchall() 
    rowDepartamentos = """ SELECT * FROM departamentos """
    cursor.execute(rowDepartamentos)
    listaDepa = cursor.fetchall()
    return render_template('home.html', tickets=row, departamentos=listaDepa, current_user_fullname= current_user.fullname)

@app.route('/deleteTicket/<int:id_ticket>', methods=['GET'])
@login_required
def deleteTicket(id_ticket):
    if request.method == 'GET':
        flash("El ticket se ha eliminado exitosamente !", "success")
        cursor = db.connection.cursor()
        sql = """ DELETE FROM tickets WHERE id_ticket = '{}'""".format(id_ticket)
        cursor.execute(sql)
        return redirect(url_for('home'))
    else:
        return "<h1>Algo pasó</h1>"
    

    
@app.route('/panelAdministracion', methods=['GET', 'POST'])
@login_required
def panelAdmin():
    if current_user.fullname == "ADMINISTRADOR" and (request.method == "GET" or request.method == "POST"):
        cursor = db.connection.cursor()
        sql = "SELECT * FROM problemas"
        cursor.execute(sql)
        row = cursor.fetchall()
        if request.method == 'POST':
            tipo_problema = request.form['tipo_problema']
            nuevo_problema = request.form['otro_tipo_problema']
            id_ticket = request.form['id_ticket']
            if nuevo_problema == '':
                sql = "UPDATE tickets SET tipo_problema = '{}' WHERE id_ticket = '{}'".format(tipo_problema, id_ticket)
                cursor.execute(sql)
                return redirect(url_for('panelAdmin'))
            else:
                sql = "INSERT INTO problemas (problema) VALUES ('{}')".format(nuevo_problema)
                cursor.execute(sql)
                sql = "UPDATE tickets SET tipo_problema = '{}' WHERE id_ticket = '{}'".format(nuevo_problema, id_ticket)
                cursor.execute(sql)
                return redirect(url_for('panelAdmin'))
        return render_template('panel/panelAdmin.html', current_user_fullname=current_user.fullname, problemas=row)
    else:
        return "<h1>No tienes permiso de acceso a esta pagina</h1>"

@app.route('/estadoTicket', methods=['POST', 'GET'])
@login_required
def cambioEstado():
    if current_user.fullname == "ADMINISTRADOR" and (request.method == "GET" or request.method == "POST"):
        id_ticket = request.form['id_ticket_estado']
        estado = request.form['estado']
        print(f"ESTE ES EL ESTADO QUE ESTA ENVIAMDO {estado}")
        cursor = db.connection.cursor()
        sql = """ UPDATE tickets SET estado = '{}' WHERE id_ticket = '{}' """.format(estado, id_ticket)
        cursor.execute(sql)
        return redirect(url_for('panelAdmin'))
    else:
        return "<h1>No tienes permiso de acceso a esta pagina</h1>"

@app.route('/enviar_respuesta', methods=['POST'])
@login_required
def enviar_respuesta():
    cursor = db.connection.cursor()
    mensaje = request.form['mensaje']
    hora_mensaje = request.form['hora_mensaje']
    id_ticket = request.form['id_ticket']
    usuario = current_user.fullname
    sql = "INSERT INTO mensajes (id_ticket, mensaje, hora_mensaje, user) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql, (id_ticket, mensaje, hora_mensaje, usuario))
    db.connection.commit()  # Confirmar los cambios
    cursor.close()  # Cerrar el cursor
    return jsonify({'message': 'Mensaje enviado correctamente'})





@app.route('/panelAdministracion/usuarios')
@login_required
def usuariosPanel():
    if current_user.fullname == "ADMINISTRADOR" and request.method == "GET" or request.method == "POST":
        listaUsuarios = ModelUser.allUsers(db)
        return render_template('panel/usuariosPanel.html', filas=listaUsuarios)
    else:
        return "<h1>No tienes permiso de acceso a esta pagina</h1>"


@app.route('/newUser', methods=['GET', 'POST'])
@login_required
def newUser():
    if current_user.fullname == "ADMINISTRADOR" and request.method == "GET" or request.method == "POST":
        flash("Se ha creado un nuevo usuario !", "success")
        username = request.form['username']
        password = request.form['password']
        fullname = request.form['fullname']
        nuevoUsuario = ModelUser.newUser(db, username, password, fullname)
        return redirect(url_for('usuariosPanel'))
    else:
        return "<h1>No tienes permiso de acceso a esta pagina</h1>"
        


@app.route('/delete/<int:id_data>', methods=['GET'])
def deleteUsuario(id_data):
    if current_user.fullname == "ADMINISTRADOR" and request.method == "GET" or request.method == "POST":
        flash("Usuario eliminado exitosamente !", "success")
        cursor = db.connection.cursor()
        sql = """ DELETE FROM user WHERE id='{}'""".format(id_data)
        cursor.execute(sql)
        return redirect(url_for('usuariosPanel'))
    else:
        return "<h1>No tienes permiso de acceso a esta pagina</h1>"
        

@app.route('/updateUsuario', methods=['POST', 'GET'])
@login_required
def updateUsuario():
    if current_user.fullname == "ADMINISTRADOR" and request.method == "GET" or request.method == "POST":
        flash("Usuario editado exitosamente !","success")
        id_data = request.form['id']
        username = request.form['username']
        password = request.form['password']
        fullname = request.form['fullname']
        updateSql = ModelUser.editUser(db, username, password, fullname, id_data)
        return redirect(url_for('usuariosPanel'))
    else:
        return "<h1>No tienes permiso de acceso a esta pagina</h1>"
        
        
        
@app.route('/panelAdministracion/departamentos')
@login_required
def departamentosPanel():
    if current_user.fullname == "ADMINISTRADOR" and request.method == "GET" or request.method == "POST":
        cursor = db.connection.cursor()
        sql = """SELECT * FROM departamentos"""
        cursor.execute(sql)
        listaDepartamentos = cursor.fetchall()
        return render_template('panel/departamentosPanel.html', departamentos= listaDepartamentos)
    else:
        return "<h1>No tienes permiso de acceso a esta pagina</h1>"
        


@app.route('/newDepartamento', methods=['GET', 'POST'])
@login_required
def nuevoDepartamento():
    if current_user.fullname == "ADMINISTRADOR" and request.method == "GET" or request.method == "POST":
        flash("Se ha creado un nuevo departamento !", "success")
        departamento = request.form['departamento']
        cursor = db.connection.cursor()
        sql = """INSERT INTO departamentos (iddepartamento, departamento)
                    VALUES (null, '{}')""".format(departamento)
        cursor.execute(sql)
        return redirect(url_for('departamentosPanel'))
    else:
        return "<h1>No tienes permiso de acceso a esta pagina</h1>"
    
@app.route('/deleteDepartamento/<int:id_data>', methods=['GET'])
@login_required
def deleteDepartamento(id_data):
    if current_user.fullname == "ADMINISTRADOR" and request.method == "GET" or request.method == "POST":
        flash("Departamento eliminado exitosamente !", "success")
        cursor = db.connection.cursor()
        sql = """ DELETE FROM departamentos WHERE iddepartamento='{}'""".format(id_data)
        cursor.execute(sql)
        return redirect(url_for('departamentosPanel'))
    else:
        return "<h1>No tienes permiso de acceso a esta pagina</h1>"
        

@app.route('/updateDepartamento', methods=['GET', 'POST'])
@login_required
def updateDepartamento():
    if current_user.fullname == "ADMINISTRADOR" and request.method == "GET" or request.method == "POST":
        flash("Departamento editado exitosamente !", "success")
        id_data = request.form['id']
        departamento = request.form['departamento']
        cursor = db.connection.cursor()
        sql = """UPDATE departamentos SET departamento='{}' 
                    WHERE iddepartamento='{}' """.format(departamento, id_data)
        cursor.execute(sql)
        return redirect(url_for('departamentosPanel'))
    else:
        return "<h1>No tienes permiso de acceso a esta pagina</h1>"


def status_401(error):
    return redirect(url_for('login'))


def status_404(error):
    return "<h1>Página no encontrada</h1>", 404


@app.route('/dataTickets', methods=['GET'])
@login_required
def dataTickets():
    cursor = db.connection.cursor()
    sql = """SELECT id_ticket, user_id, user_fullname, departamento,
            numero_contacto, descripcion, estado, created_at, tipo_problema descripcion FROM tickets """
    tickets = cursor.execute(sql)
    data = cursor.fetchall()
    response_data = {"data": []}
    for row in data:
        response_data["data"].append({"id_ticket": row[0], "user_id": row[1],
                                      "user_fullname": row[2], "departamento": row[3],
                                      "numero_contacto": row[4], "descripcion": row[5],
                                      "estado": row[6], "created_at": row[7], "tipo_problema": row[8]})
    return jsonify(response_data)


@app.route('/ticketUser/<int:user_id>', methods=['GET'])
@login_required
def misTickets(user_id):
    cursor = db.connection.cursor()
    sql = """ SELECT id_ticket, user_fullname, departamento, numero_contacto, descripcion, estado, created_at FROM tickets 
            WHERE user_id = '{}'""".format(user_id)
    cursor.execute(sql)
    tickets = cursor.fetchall()
    response_tickets = {"data": []}
    for row in tickets:
        response_tickets['data'].append({"id_ticket": row[0],"user_fullname": row[1],"departamento": row[2],"numero_contacto": row[3],"descripcion": row[4],"estado": row[5],"created_at": row[6]})
    return jsonify(response_tickets)

@app.route('/dataGrafico', methods=['GET'])
@login_required
def dataGrafico():
    cursor = db.connection.cursor()
    sql = """ SELECT tipo_problema FROM tickets """
    cursor.execute(sql)
    datos = cursor.fetchall()

    # Contar la frecuencia de cada tipo de problema
    frecuencias = defaultdict(int)
    for row in datos:
        tipo_problema = row[0]
        frecuencias[tipo_problema] += 1

    # Ordenar los resultados por frecuencia
    resultados = sorted(frecuencias.items(), key=lambda x: x[1], reverse=True)

    # Preparar la respuesta en formato JSON
    response_data = {"data": []}
    for tipo_problema, frecuencia in resultados:
        response_data['data'].append({"tipo_problema": tipo_problema, "frecuencia": frecuencia})

    return jsonify(response_data)

@app.route('/estadisticas-problemas')
@login_required
def estadisticas_problemas():
    return render_template('grafico.html')
    
@app.route('/ver-ticket/<int:id_ticket>', methods=['GET'])
@login_required
def verTicket(id_ticket):
    cursor = db.connection.cursor()
    sql = """ SELECT user_fullname, departamento, numero_contacto, descripcion, estado, 
            created_at, tipo_problema FROM tickets WHERE id_ticket = '{}' """.format(id_ticket)
    ticket = cursor.execute(sql)
    dataTicket = cursor.fetchone()
    if dataTicket:
        response_data = {
            "user_fullname": dataTicket[0],
            "departamento": dataTicket[1],
            "numero_contacto": dataTicket[2],
            "descripcion": dataTicket[3],
            "estado": dataTicket[4],
            "created_at": dataTicket[5],
            "tipo_problema": dataTicket[6]
        }
        return jsonify(response_data)
    else:
        return jsonify({"error": "Ticket no encontrado"})
    
@app.route('/obtener_mensajes/<int:id_ticket>', methods=['GET'])
@login_required
def obtener_mensajes(id_ticket):
    cursor = db.connection.cursor()
    cursor.execute("SELECT * FROM mensajes WHERE id_ticket = '{}' order by str_to_date(hora_mensaje, '%%Y-%%m-%%d %%H:%%i:%%s') asc".format(id_ticket))
    mensajes = cursor.fetchall()
    cursor.close()
    if mensajes:
        mensajes_json = [{'mensaje': m[1], 'hora_mensaje': m[2], 'user': m[3]} for m in mensajes[::-1]]
        return jsonify(mensajes_json)
    else:
        return jsonify({"Error": "Creo que no hemos encontrado lo que buscamos"})


app.register_error_handler(401, status_401)
app.register_error_handler(404, status_404)
app.config.from_object(config['development'])
csrf.init_app(app)
if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=5000)
    app.run(debug=True)