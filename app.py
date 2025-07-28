from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from flasgger import Swagger
from extensions import db, limiter
import os

# Load .env
load_dotenv()

# App init
app = Flask(__name__)
CORS(app)
Swagger(app)

# Config
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Init extensions
from extensions import db, limiter
db.init_app(app)
limiter.init_app(app)

# **Ensure all models are imported so SQLAlchemy knows about them**
import models

# Register grouped routes
from routes import bp as routes_bp
app.register_blueprint(routes_bp, url_prefix='/api')

# Users route
from routes.users import users_bp
app.register_blueprint(users_bp, url_prefix='/users')

@app.route('/')
def index():
    return {"status": "XCloudBot backend running!"}

if __name__ == '__main__':
    app.run(debug=True)
