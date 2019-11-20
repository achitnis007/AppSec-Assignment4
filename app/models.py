from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(16), unique=False, nullable=False)
    # salt = db.Column(String(16), nullable=False)
    service_history_records = db.relationship("UserServiceHistory", backref="user")
    login_history_records = db.relationship("UserLoginHistory", backref="'user")

    def __repr__(self):
        return "User('{self.username}', '{self.phone}')"


class UserLoginHistory(db.Model):
    __tablename__ = 'user_login_history'
    id =  db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_login = db.Column(db.DateTime, nullable=False)
    time_logout = db.Column(db.DateTime, nullable=True)
    # user_record = db.relationship('User', backpopulates='user_login_history', lazy=True)

    def __repr__(self):
        return "UserLoginHistory('{self.id}', '{self.user_id}', '{self.time_login}', '{self.time_logout}')"


class UserServiceHistory(db.Model):
    __tablename__ = 'user_service_history'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now)
    input_content = db.Column(db.Text, nullable=False)
    misspelled_content = db.Column(db.Text, nullable=True)
    # user_record = db.relationship('User', backpopulates='user_service_history', lazy=True)

    def __repr__(self):
        return "UserServiceHistory('{self.id}', '{self.user_id}', '{self.date_posted}', '{self.input_content}', '{self.misspelled_content}')"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))