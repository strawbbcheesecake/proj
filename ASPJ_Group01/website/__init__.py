import pymysql
from flask import Flask, g, flash
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from .config import Config
from flask_wtf.csrf import generate_csrf
from .auth import mail
from .models import db
from datetime import timedelta

UPLOAD_FOLDER = 'website/static'


pymysql.install_as_MySQLdb()

def create_app():
    csrf = CSRFProtect()
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "qwertyuiop"  # Ensure this is a string
    csrf.init_app(app)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Ilovec0ding_@localhost/website'

    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'Kjiaxuan2005@gmail.com'
    app.config['MAIL_PASSWORD'] = 'ship sxcc ucjg mjeh'
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)
    db.init_app(app)


    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    app.config.from_object(Config)

    def get_db(account='jx'):
        if 'db' not in g:
            account_config = app.config['DATABASE_CONFIG'].get(account)
            if account_config is None:
                raise Exception(f"Unknown account: {account}")
            else:
                print(f"Connecting to MySQL database: {account}")
            try:
                g.mydb = pymysql.connect(
                    host=account_config['host'],
                    user=account_config['user'],
                    passwd=account_config['password'],
                    database=account_config['database'],
                )
                print('Connected to MySQL database using account:', account)
            except Exception as e:
                flash('Error connecting to MySQL database', category='error')
                print(e)
            return g.mydb

    @app.before_request
    def before_request():
        g.mydb = get_db()
        g.csrf_token = generate_csrf()

    @app.teardown_request
    def teardown_request(exception):
        mydb = g.pop('mydb', None)
        if mydb is not None:
            mydb.close()
            print('Disconnected from MySQL database')

    mail.init_app(app)

    print('Created Flask application!')

    from .views import views
    from .auth import auth
    from .shop import shop

    app.register_blueprint(views, url_prefix='')
    app.register_blueprint(auth, url_prefix='')
    app.register_blueprint(shop, url_prefix='')

    from .models import User

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app
