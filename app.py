from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_mysqldb import MySQL
from flask_wtf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from config import config, DevelopmentConfig
import json
from collections import defaultdict
from flask_mail import Mail, Message
from smtplib import SMTPException
from itsdangerous import URLSafeTimedSerializer
import ssl
from werkzeug.security import check_password_hash, generate_password_hash
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

#flask mail settings
app.config['MAIL_SERVER'] = 'smtp.office365.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'soporteTicket@outlook.es'
app.config['MAIL_PASSWORD'] = 'admin.2023!'
app.config['MAIL_DEFAULT_SENDER'] = ('AdministradorTickets', 'soporteTicket@outlook.es' )
mail = Mail(app)

app.config.from_object(DevelopmentConfig)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

@login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(db, id)


@app.route('/test', methods=['GET', 'POST'])
def test():
    return render_template('test.html')

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
                if logged_user.password and logged_user.fullname is None:
                    flash("Hey tu rut está habilitado para el uso del sistema pero necesitas registrarte", "warning")
                    return redirect(url_for('registrarse'))
                elif logged_user.password and logged_user.email_confirmed == 1:
                    login_user(logged_user)
                    return redirect(url_for('home'))
                elif logged_user.password and logged_user.email_confirmed == 0:
                    flash("El correo electronico no ha sido confirmado aun !!", "warning")
                    return redirect(url_for('login'))
                else:
                    flash("Contraseña incorrecta...", 'danger')
                    return render_template('auth/login.html')
        else:
            flash("Usuario no encontrado...", "danger")
            return render_template('auth/login.html')
    else:
        return render_template('auth/login.html')
    
@app.route('/cambiar-contraseña', methods=['GET', 'POST'])
def cambiarContraseña():
    rut = None
    if request.method == 'POST':
        rut = request.form['rut']
        if not rut:
            flash('Por favor, indique su rut', 'warning')
            return redirect(url_for('cambiarContraseña'))
        cursor = db.connection.cursor()
        sql = """ SELECT password, email FROM user WHERE username = '{}' """.format(rut)
        cursor.execute(sql)
        result = cursor.fetchone()
        if result:
            contraseña, email = result
            try:
                token = serializer.dumps(email, salt='cambiar_contraseña')
                msg = Message('Problema contraseña Sistema de tickets', recipients=[email])
                link = url_for('confirm_contraseña', token=token, rut=rut, _external=True)
                msg.body = 'Este es un mensaje automatizado para cambiar su contraseña!\n {}'.format(link)
                mail.send(msg)
                flash('Se ha enviado un correo electrónico para cambiar su contraseña', 'success')
                return redirect(url_for('login'))
            except SMTPException as e:
                flash('Ha ocurrido un error al enviar el correo electrónico, intente mas tarde', 'danger')
                print(e)
        else:
            flash('El rut ingresado no existe', 'danger')
        
    return render_template('/auth/cambiar_contraseña.html', rut=rut)

@app.route('/confirmar-contraseña/<token>/<rut>', methods=['GET', 'POST'])
def confirm_contraseña(token, rut):
    try:
        contraseña = serializer.loads(token, salt='cambiar_contraseña', max_age=300)
    except:
        flash('El enlace de confirmacion no es valido o ha caducado', 'warning')
        return redirect(url_for('login'))
    if request.method == 'POST':
        contraseñaForm = request.form['password-confirm']
        hashedPassword = generate_password_hash(contraseñaForm)
        cursor = db.connection.cursor()
        sql = """ UPDATE user SET password = '{}' WHERE username = '{}' """.format(hashedPassword, rut)
        cursor.execute(sql)
        flash('La contraseña se ha cambiado satisfactoriamente', 'success')
        return redirect(url_for('login'))
    return render_template('/auth/formNuevaContraseña.html', token=token, rut=rut)

@app.route('/registrarse', methods=['GET', 'POST'])
def registrarse():
    return render_template("/auth/verificarRut.html")

@app.route('/verificarRut', methods=['GET', 'POST'])
def verificarRut():
    crear_usuario = False  # establecer la variable de contexto en False
    if request.method == 'POST':
        rut = request.form['rut']
        cursor = db.connection.cursor()
        sql = """SELECT * FROM user WHERE username = '{}' """.format(rut)
        cursor.execute(sql)
        user = cursor.fetchone()
        if user is not None:
            sql = """ SELECT password FROM user WHERE username = '{}'  """.format(rut)
            cursor.execute(sql)
            password = cursor.fetchone()
            if password[0] is None:
                crear_usuario = True  # establecer la variable de contexto en True
                flash("Porfavor completar el siguiente formulario para poder registrarse", "warning")
                return redirect(url_for('registrarFuncionario', rut=rut, crear_usuario=crear_usuario))
            else:
                flash("Este rut ya registra dentro de nuestro sistema con una cuenta existente", "danger")
                return redirect(url_for('login'))
        else:
            crear_usuario = True  # establecer la variable de contexto en True
            flash("El RUT está disponible.", "success")
    
    # Pasar la variable de contexto a la plantilla
    return render_template('/auth/register.html', crear_usuario=crear_usuario)


from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/registrarFuncionario/<rut>/<crear_usuario>', methods=['GET', 'POST'])
def registrarFuncionario(rut, crear_usuario):
    if request.method == 'POST':
        fullname = request.form['fullname']
        password = request.form['password-confirm']
        email = request.form['email']
        cursor = db.connection.cursor()
        sql = """SELECT id FROM user WHERE email = '{}'""".format(email)
        cursor.execute(sql)
        result = cursor.fetchone()
        if result:
            flash('La dirección de correo electrónico ya está en uso', 'warning')
            return redirect(url_for('registrarFuncionario', rut=rut, crear_usuario=crear_usuario))
        else:
            hashed_password = generate_password_hash(password)
            token = serializer.dumps(email, salt='confirm-email')
            cursor.execute("UPDATE user SET fullname=%s, email=%s, password=%s, token=%s, token_expiration=%s WHERE username=%s", (fullname, email, hashed_password, token, datetime.utcnow() + timedelta(hours=24), rut))
            db.connection.commit()
            cursor.close()
            flash('Se ha enviado un mensaje de confirmación a su correo electrónico', 'success')
            msg = Message('Confirmar correo electrónico', recipients=[email])
            link = url_for('confirm_email', token=token, _external=True)
            msg.body = 'Para confirmar su correo electrónico, haga clic en el siguiente enlace:\n {}'.format(link)
            mail.send(msg)
            return redirect(url_for('login'))
    return render_template('/auth/register.html', crear_ususario=crear_usuario)

@app.route('/confirmar/<token>')
def confirm_email(token):
    try:
        email = serializer.loads(token, salt='confirm-email', max_age=300)
    except:
        flash('El enlace de confirmación no es válido o ha caducado', 'warning')
        return redirect(url_for('login'))
    cursor = db.connection.cursor()
    sql = """SELECT id FROM user WHERE email = '{}'""".format(email)
    cursor.execute(sql)
    result = cursor.fetchone()
    if not result:
        flash('La dirección de correo electrónico no existe', 'warning')
        return redirect(url_for('login'))
    else:
        cursor.execute("UPDATE user SET email_confirmed = %s, token = NULL, token_expiration = NULL WHERE email = %s", (True, email))
        db.connection.commit()
        cursor.close()
        flash('La dirección de correo electrónico ha sido confirmada', 'success')
        msg = Message('Confirmación de correo electrónico',  recipients=[email])
        msg.body = 'Su correo electrónico ha sido confirmado exitosamente.'
        mail.send(msg)
        return redirect(url_for('login'))

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
        flash("El ticket se ha cerrado exitosamente !", "success")
        cursor = db.connection.cursor()
        sql = """UPDATE tickets SET estado = 'Cerrado' WHERE id_ticket = '{}'""".format(id_ticket)
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
        return render_template("/errores/noAcceso.html")

@app.route('/estadoTicket', methods=['POST', 'GET'])
@login_required
def cambioEstado():
    if current_user.fullname == "ADMINISTRADOR" and (request.method == "GET" or request.method == "POST"):
        id_ticket = request.form['id_ticket_estado']
        estado = request.form['estado']
        cursor = db.connection.cursor()
        sql = """ UPDATE tickets SET estado = '{}' WHERE id_ticket = '{}' """.format(estado, id_ticket)
        cursor.execute(sql)
        return redirect(url_for('panelAdmin'))
    else:
        return render_template("/errores/noAcceso.html")

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
        return render_template("/errores/noAcceso.html")


@app.route('/newUser', methods=['GET', 'POST'])
@login_required
def newUser():
    if current_user.fullname == "ADMINISTRADOR" and request.method == "GET" or request.method == "POST":
        flash("Se ha creado un nuevo usuario !", "success")
        rut = request.form['rut']
        nuevoUsuario = ModelUser.newUser(db, rut)
        return redirect(url_for('usuariosPanel'))
    else:
        return render_template("/errores/noAcceso.html")
        


@app.route('/delete/<int:id_data>', methods=['GET'])
def deleteUsuario(id_data):
    if current_user.fullname == "ADMINISTRADOR" and request.method == "GET" or request.method == "POST":
        flash("Usuario eliminado exitosamente !", "success")
        cursor = db.connection.cursor()
        sql = """ DELETE FROM user WHERE id='{}'""".format(id_data)
        cursor.execute(sql)
        return redirect(url_for('usuariosPanel'))
    else:
        return render_template("/errores/noAcceso.html")
        

@app.route('/updateUsuario', methods=['POST', 'GET'])
@login_required
def updateUsuario():
    if current_user.fullname == "ADMINISTRADOR" and request.method == "GET" or request.method == "POST":
        flash("Usuario editado exitosamente !","success")
        id_data = request.form['id']
        username = request.form['username']
        email = request.form['email']
        fullname = request.form['fullname']
        updateSql = ModelUser.editUser(db, username, email, fullname, id_data)
        return redirect(url_for('usuariosPanel'))
    else:
        return render_template("/errores/noAcceso.html")
        
        
        
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
        return render_template("/errores/noAcceso.html")
        


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
        return render_template("/errores/noAcceso.html")
    
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
        return render_template("/errores/noAcceso.html")
        

@app.route('/updateDepartamento', methods=['GET', 'POST'])
@login_required
def updateDepartamento():
    if current_user.fullname == "ADMINISTRADOR" and request.method == "GET" or request.method == "POST":
        flash("Departamento editado exitosamente !", "success")
        id_depa = request.form['iddepa']
        departamento = request.form['departamento']
        cursor = db.connection.cursor()
        sql = """UPDATE departamentos SET departamento='{}' 
                    WHERE iddepartamento='{}' """.format(departamento, id_depa)
        cursor.execute(sql)
        return redirect(url_for('departamentosPanel'))
    else:
        return render_template("/errores/noAcceso.html")





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


@app.route('/obtener_usuarios', methods=['GET'])
@login_required
def obtener_usuarios():
    cursor = db.connection.cursor()
    sql = """SELECT id, username, fullname, email FROM user"""
    cursor.execute(sql)
    dataUser = cursor.fetchall()
    if dataUser:
        response_data = {"data": []}
        for user in dataUser:
           response_data['data'].append({"id": user[0], "username": user[1], "fullname": user[2],
                                         "email": user[3]})
        return jsonify(response_data)
    else:
        return jsonify({"Error": "Usuarios no encontrados"})

@app.route('/editar_usuario/<int:id>')
@login_required
def editar_usuarios(id):
    cursor =  db.connection.cursor()
    sql = """ SELECT id, username, fullname, email FROM user WHERE id = '{}' """.format(id)
    cursor.execute(sql)
    dataUser = cursor.fetchone()
    if dataUser:
        response_data = {
            "id": dataUser[0],
            "username": dataUser[1],
            "fullname": dataUser[2],
            "email": dataUser[3]
        }
        return jsonify(response_data)
    else:
        return jsonify({"Error": "El usuario no se ha encontrado"})
    
    
@app.route('/obtener_departamentos', methods=['GET'])
@login_required
def obtener_departamentos():
    cursor = db.connection.cursor()
    sql = """ SELECT iddepartamento, departamento from departamentos """
    cursor.execute(sql)
    dataDepa = cursor.fetchall()
    if dataDepa:
        response_data = {"data": []}
        for depa in dataDepa:
            response_data['data'].append({"iddepartamento": depa[0], "departamento": depa[1]})
        return jsonify(response_data)
    else:
        return jsonify({"Error": "Departamentos no encontrados"})
            
@app.route('/editar_departamento/<int:departamento_id>')
@login_required
def editar_departamento(departamento_id):
    cursor =  db.connection.cursor()
    sql = """ SELECT iddepartamento, departamento FROM departamentos WHERE iddepartamento = '{}' """.format(departamento_id)
    cursor.execute(sql)
    dataDepa = cursor.fetchone()
    if dataDepa:
        response_data = {
            "iddepartamento": dataDepa[0],
            "departamento": dataDepa[1],
        }
        return jsonify(response_data)
    else:
        return jsonify({"Error": "El departamento no se ha encontrado"})

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
    cursor.execute("SELECT * FROM mensajes WHERE id_ticket = '{}' order by str_to_date(hora_mensaje, '%%Y-%%m-%%d %%H:%%i:%%s') ASC".format(id_ticket))
    mensajes = cursor.fetchall()
    cursor.close()
    if mensajes:
        mensajes_json = [{'mensaje': m[1], 'hora_mensaje': m[2], 'user': m[3]} for m in mensajes]
        return jsonify(mensajes_json)
    else:
        return jsonify({"Error": "Creo que no hemos encontrado lo que buscamos"})
    

def status_401(error):
    return redirect(url_for('login'))


def status_404(error):
    return "<h1>Página no encontrada</h1>", 404

app.register_error_handler(401, status_401)
app.register_error_handler(404, status_404)
app.config.from_object(config['development'])
csrf.init_app(app)
if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=5000)
    app.run(debug=True)