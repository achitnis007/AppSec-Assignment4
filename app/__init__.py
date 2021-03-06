from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_talisman import Talisman

name = "app"

app = Flask(__name__)

SELF = "'self'"

Talisman(
    app,
    content_security_policy={
        'default-src': SELF,
        'script-src': [
            SELF,
            'code.jquery.com',
            'cdnjs.cloudflare.com',
            'stackpath.bootstrapcdn.com'
        ],
        'style-src': [
            SELF,
            'code.jquery.com',
            'cdnjs.cloudflare.com',
            'stackpath.bootstrapcdn.com'
        ],
        'Strict-Transport-Security': 'max-age=0; includeSubDomains'
    },
    content_security_policy_nonce_in=['script-src']
)

secretspath = "/run/secrets/"
_ = open(secretspath+'csrf_key', 'r'); csrf_key = _.read().replace('\n', ''); _.close()

app.config['SECRET_KEY'] = csrf_key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

from app import db

bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from app import routes
