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
# app.config['SECRET_KEY'] = '7110c8ae51a4b5af97be6534caef90e4bb9bdcb3380af008f90b23a5d1616bf319bc298105da20fe'
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = ''
# app.config['MYSQL_DB'] = 'flask_login'

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
                    return redirect(url_for('panelControl'))
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


@app.route('/home2')
@login_required
def home2():
    return render_template('home2.html')


@app.route('/nuevoTicket')
@login_required
def nuevoticket():
    return render_template('formularioTicket.html')

@app.route('/home')
@login_required
def home():
    return render_template('home.html')

@app.route('/panelControl')
@login_required
def panelControl():
    return render_template('panelControl.html')


@app.route('/protected')
@login_required
def protected():
    return "<h1>Esta es una vista protegida, solo para usuarios autenticados.</h1>"


@app.route('/heroku')
def heroku():
    return render_template('herokuPrueba.html')

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
