from flask import Flask
import os
from photo import photo
from login_register import login_register
UPLOAD_FOLDER = os.path.join('static', 'photoDump')

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.register_blueprint(photo)
app.register_blueprint(login_register)