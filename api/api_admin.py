from functools import wraps
from time import sleep

from flask import Blueprint, jsonify, make_response, request, session
from werkzeug.security import check_password_hash

from crud import crud
from settings import ADMIN, HPSW

api_admin = Blueprint("api_admin", __name__, url_prefix="/api/admin")


def login_admin():
    session["admin_logged"] = 1


def is_logged():
    return True if session.get("admin_logged") else False


def logout_admin():
    session.pop("admin_logged", None)


def login_req(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if is_logged():
            return func(*args, **kwargs)
        return jsonify(message="login required"), 401

    return wrapper


@api_admin.route("/")
def index():
    return jsonify(message="hello api admin. there's nothing here ツ"), 418


# POST admin + psw
@api_admin.route("/login", methods=["POST"])
def login():
    if is_logged():
        return jsonify(message="already logged")

    admin = request.form.get("admin")
    psw = request.form.get("psw")
    if not all([admin, psw]):
        return jsonify(message="expected: admin/psw"), 400

    sleep(1)
    if admin == ADMIN and check_password_hash(HPSW, psw):
        login_admin()
        response = make_response({"message": "admin login"})
        response.set_cookie("user_id", "admin")
        return response

    return jsonify(message="invalid admin/password"), 401


# GET
@api_admin.route("/logout")
def logout():
    if is_logged():
        logout_admin()
    response = make_response({"message": "admin logout"})
    response.delete_cookie("user_id")
    response.delete_cookie("session")
    return response


# GET
@api_admin.route("/settings")
@login_req
def settings():
    return jsonify(admin=ADMIN)


# GET
@api_admin.route("/user")
@login_req
def user():
    res = crud.get_user_all()
    return jsonify(res)


# POST psw, exp_date, active(0|1)
@api_admin.route("/user/<int:user_id>", methods=["GET", "POST"])
@login_req
def user_edit(user_id):
    if request.method == "POST":
        res = crud.edit_user(user_id, request.form)
        return jsonify(message="success", user=res), 201

    user = crud.get_user(user_id)  # -> object
    return jsonify(user.as_dict())


# POST email
@api_admin.route("/user/del", methods=["POST"])
@login_req
def user_del():
    crud.del_user(request.form.get("email"))
    return jsonify(), 204


# GET prompt_id, limit + page
@api_admin.route("/user/<int:user_id>/content")
@login_req
def content(user_id):
    res = crud.get_content_all(user_id, request.args)
    return jsonify(res)


# GET limit + page
@api_admin.route("/user/<int:user_id>/prompt")
@login_req
def prompt(user_id):
    res = crud.get_prompt_all(user_id, request.args)
    return jsonify(res)


# POST name + type
@api_admin.route("/pflist", methods=["GET", "POST"])
@login_req
def pf_list():
    if request.method == "POST":
        res = crud.add_prompt_field_list(
            request.form.get("name"), request.form.get("type")
        )
        return jsonify(message="success", field=res), 201

    res = crud.get_prompt_field_list_all()
    return jsonify(res)


# POST name
@api_admin.route("/pflist/del", methods=["POST"])
@login_req
def pf_list_del():
    crud.del_prompt_field_list(request.form.get("name"))
    return jsonify(), 204


# POST name(main|pfield|style|language) + value, ?column(value|note|default)
@api_admin.route("/pmods", methods=["GET", "POST"])
@login_req
def prompt_mods():
    if request.method == "POST":
        res = crud.edit_prompt_mod(
            request.form.get("name"),
            request.form.get("value"),
            column=request.form.get("column"),
        )
        return jsonify(message="success", prompt_mod=res), 201

    res = crud.get_prompt_mod_all()
    return jsonify(res)
