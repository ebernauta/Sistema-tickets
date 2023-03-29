from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from flask_wtf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, login_required

from config import config

# Models:
from models.ModelUser import ModelUser


# Entities:
from models.entities.User import User


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



@app.route('/nuevoTicket')
@login_required
def nuevoticket():
    return render_template('formularioTicket.html')

@app.route('/home')
@login_required
def home():
    return render_template('home.html')

# @app.route('/loginPanel', methods=['GET', 'POST'])
# @login_required
# def loginPanel():
#     if request.method == 'POST':
#         contraseñaPanel = request.form['contraseñaPanel']
#         cursor = db.connection.cursor()
#         sql = """SELECT panelAdmin FROM admin WHERE panelAdmin = '{}'""".format(contraseñaPanel)
#         cursor.execute(sql)
#         row = cursor.fetchone()
#         if row != None:
#             return redirect(url_for('panelAdmin'))
#             print("debajo del redirect")
#         else:
#             flash("Contraseña maestra incorrecta...", 'danger')
#             return render_template('auth/loginPanel.html')
#     else:
#         return render_template('auth/loginPanel.html') 

@app.route('/panelAdministracion', methods=['GET', 'POST'])
@login_required
def panelAdmin():
    return render_template('panel/panelAdmin.html')
    
   

@app.route('/panelAdministracion/usuarios')
@login_required
def usuariosPanel():
    listaUsuarios = ModelUser.allUsers(db)
    print(listaUsuarios)
    return render_template('panel/usuariosPanel.html', filas=listaUsuarios)

@app.route('/newUser', methods=['GET', 'POST'])
@login_required
def newUser():
    if request.method == 'POST':
        flash("Se ha creado un nuevo usuario !", "success")
        username = request.form['username']
        password = request.form['password']
        fullname = request.form['fullname']
        nuevoUsuario = ModelUser.newUser(db, username, password, fullname)
        return redirect(url_for('usuariosPanel'))


@app.route('/delete/<int:id_data>', methods=['GET'])
def deleteUsuario(id_data):
    flash("Usuario eliminado exitosamente !", "success")
    cursor = db.connection.cursor()
    sql = """ DELETE FROM user WHERE id='{}'""".format(id_data)
    cursor.execute(sql)
    return redirect(url_for('usuariosPanel'))

@app.route('/updateUsuario', methods=['POST', 'GET'])
@login_required
def updateUsuario():
    if request.method == 'POST':
        flash("Usuario editado exitosamente !","success")
        id_data = request.form['id']
        username = request.form['username']
        password = request.form['password']
        fullname = request.form['fullname']
        updateSql = ModelUser.editUser(db, username, password, fullname, id_data)
        return redirect(url_for('usuariosPanel'))
        
        
@app.route('/panelAdministracion/departamentos')
@login_required
def departamentosPanel():
    cursor = db.connection.cursor()
    sql = """SELECT * FROM departamentos"""
    cursor.execute(sql)
    listaDepartamentos = cursor.fetchall()
    print(listaDepartamentos)
    return render_template('panel/departamentosPanel.html', departamentos= listaDepartamentos)


@app.route('/newDepartamento', methods=['GET', 'POST'])
@login_required
def nuevoDepartamento():
    if request.method == 'POST':
        flash("Se ha creado un nuevo departamento !", "success")
        departamento = request.form['departamento']
        cursor = db.connection.cursor()
        sql = """INSERT INTO departamentos (iddepartamento, departamento)
                    VALUES (null, '{}')""".format(departamento)
        cursor.execute(sql)
        return redirect(url_for('departamentosPanel'))
    
@app.route('/deleteDepartamento/<int:id_data>', methods=['GET'])
@login_required
def deleteDepartamento(id_data):
    flash("Departamento eliminado exitosamente !", "success")
    cursor = db.connection.cursor()
    sql = """ DELETE FROM departamentos WHERE iddepartamento='{}'""".format(id_data)
    cursor.execute(sql)
    return redirect(url_for('departamentosPanel'))

@app.route('/updateDepartamento', methods=['GET', 'POST'])
@login_required
def updateDepartamento():
    if request.method == 'POST':
        flash("Departamento editado exitosamente !", "success")
        id_data = request.form['id']
        departamento = request.form['departamento']
        cursor = db.connection.cursor()
        sql = """UPDATE departamentos SET departamento='{}' 
                    WHERE iddepartamento='{}' """.format(departamento, id_data)
        cursor.execute(sql)
        return redirect(url_for('departamentosPanel'))

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
