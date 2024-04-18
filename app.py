import traceback

import sentry_sdk
from flask import Flask, jsonify, render_template
from flask_login import LoginManager
from loguru import logger
from sqlalchemy.sql import text
from werkzeug.exceptions import InternalServerError

from api.api_admin import api_admin
from api.api_user import api_user
from crud import crud
from settings import DB_PATH, DEBUG, SECRET, SENTRY
from userlogin import UserLogin
from views.admin import admin
from views.user import user

sentry_sdk.init(
    dsn=SENTRY,
    # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions. We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)

logger = logger.bind(name="__main__")

DEBUG = DEBUG
SECRET_KEY = SECRET
SQLALCHEMY_DATABASE_URI = DB_PATH
SQLALCHEMY_TRACK_MODIFICATIONS = False


app = Flask(__name__)
app.config.from_object(__name__)

app.register_blueprint(admin)
app.register_blueprint(user)
app.register_blueprint(api_admin)
app.register_blueprint(api_user)

login_manager = LoginManager(app)
login_manager.user_loader(lambda id: UserLogin().fromDB(id, crud))

crud.db.init_app(app)


@app.before_request
def before_request():
    if DB_PATH.startswith("sqlite"):
        crud.db.session.execute(text("PRAGMA foreign_keys = ON"))


@app.route("/api/docs")
def api_docs():
    return render_template("api_docs.html")


@app.route("/views/")
def views():
    return render_template("login/log_base.html")


@app.errorhandler(500)
def err(e: InternalServerError):
    logger.error(traceback.format_exc(limit=-2))

    return jsonify(
        error=str(e.original_exception),
        traceback=traceback.format_exc(limit=-2),
    ), 500


if __name__ == "__main__":
    app.run()


# @app.route('/images/<path:filename>')
# @login_required  # from flask_login
# def images(filename):
#     return send_from_directory(IMG_PATH, filename)  # from flask

# Make the function available to the blueprint as current_app.func()
# app.func = func

# @login_manager.user_loader
# def load_user(id):
#     return UserLogin().fromDB(id, dbase)
