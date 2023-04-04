from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from flask_wtf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
from config import config

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



@app.route('/home/nuevoTicket', methods=['GET', 'POST'])
@login_required
def nuevoTicket():
    cursor = db.connection.cursor()
    rowDepartamentos = """ SELECT * FROM departamentos"""
    cursor.execute(rowDepartamentos)
    listaDepa = cursor.fetchall()
    return render_template('formularioTicket.html', departamentos=listaDepa)

@app.route('/generarTicket', methods=['GET', 'POST'])
@login_required
def generarTicket():
    if request.method == 'POST':
        print("SE ENVIO EL FORMULARIO Y PASÉ POR EL POST")
        cursor = db.connection.cursor()
        user_id = current_user.id
        user_fullname = current_user.fullname
        departamento = request.form['departamento']
        tipo_problema = request.form['tipoProblema']
        descripcion = request.form['descripcion']
        status = 'open'
        create_at = datetime.now()
        sql = """ INSERT INTO tickets (user_id, user_fullname, departamento, tipo_problema,
                    descripcion, estado, created_at) VALUES 
                    ('{}','{}','{}','{}','{}','{}', '{}')""".format(user_id, user_fullname ,departamento, tipo_problema,
                                                            descripcion, status, create_at)
        cursor.execute(sql)
        return redirect(url_for('nuevoTicket'))

@app.route('/home')
@login_required
def home():
    cursor = db.connection.cursor()
    sql = """SELECT id_ticket, user_fullname, departamento, tipo_problema, descripcion,
                    estado, created_at from tickets WHERE user_id = '{}' """.format(current_user.id)
    cursor.execute(sql)
    row = cursor.fetchall()
    print(row)
    return render_template('home.html', tickets=row)

@app.route('/panelAdministracion', methods=['GET', 'POST'])
@login_required
def panelAdmin():
    if current_user.fullname == "ADMINISTRADOR" and request.method == "GET" or request.method == "POST":
        return render_template('panel/panelAdmin.html')
    else:
        return "<h1>No tienes permiso de acceso a esta pagina</h1>"
    
   

@app.route('/panelAdministracion/usuarios')
@login_required
def usuariosPanel():
    if current_user.fullname == "ADMINISTRADOR" and request.method == "GET" or request.method == "POST":
        listaUsuarios = ModelUser.allUsers(db)
        print(listaUsuarios)
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
        print(listaDepartamentos)
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

@app.route('/protected')
@login_required
def protected():
    return "<h1>Esta es una vista protegida, solo para usuarios autenticados.</h1>"


def status_401(error):
    return redirect(url_for('login'))


def status_404(error):
    return "<h1>Página no encontrada</h1>", 404


app.register_error_handler(401, status_401)
app.register_error_handler(404, status_404)
app.config.from_object(config['development'])
csrf.init_app(app)
if __name__ == '__main__':
    app.run(debug=True)
