from flask import current_app

from flask_login import UserMixin
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
import jwt

db = SQLAlchemy()
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    fname = db.Column(db.String(50), nullable=False)
    lname = db.Column(db.String(50), nullable=False)
    user_type = db.Column(db.Enum("customer", "staff"), nullable=False)
    failed_login_attempts = db.Column(db.Integer, default=0)
    lockout_time = db.Column(db.DateTime, nullable=True)
    security_answer = db.Column(db.String(150), nullable=False)
    def get_reset_token(self, expires_sec=3600):
        secret_key = current_app.config['SECRET_KEY']
        expiration = datetime.utcnow() + timedelta(seconds=expires_sec)

        # Create the token
        token = jwt.encode({'user_id': self.id, 'exp': expiration}, secret_key, algorithm='HS256')
        return token

    @staticmethod
    def verify_reset_token(token):
        try:
            secret_key = current_app.config['SECRET_KEY']
            decoded_token = jwt.decode(token, secret_key, algorithms=['HS256'])
            user_id = decoded_token['user_id']
        except jwt.ExpiredSignatureError:
            print("Token has expired")
            return None
        except jwt.InvalidTokenError:
            print("Invalid token")
            return None

        return User.query.get(user_id)

    def is_locked_out(self):
        if self.lockout_time:
            return (datetime.utcnow() - self.lockout_time).seconds < 15
        return False

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", backref=db.backref("customer", uselist=False))

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", backref=db.backref("staff", uselist=False))
    role = db.Column(db.Enum("admin", "moderator", "employee"), nullable=False)

class Log(db.Model):
    __tablename__ = "LOGS"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(255))
    funcName = db.Column(db.String(255))
    lineno = db.Column(db.Integer)
    levelname = db.Column(db.String(10))
    msg = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

class Product(db.Model):
    product_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_name = db.Column(db.String(120))
    product_desc = db.Column(db.String(255))
    product_cat = db.Column(db.String(120))
    product_price = db.Column(db.Float(5, 2))

