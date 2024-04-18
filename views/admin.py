from functools import wraps
from time import sleep

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash  # , generate_password_hash

from crud import crud
from settings import ADMIN, HPSW

admin = Blueprint("admin", __name__, url_prefix="/views/admin")  # admin.index


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
        return redirect(url_for(".login"))

    return wrapper


@admin.route("/")
def index():
    return render_template("login/log_admin.html")


# POST admin, psw
@admin.route("/login", methods=["GET", "POST"])
def login():
    if is_logged():
        return redirect(url_for(".user", user=0))

    if request.method == "POST":
        sleep(1)
        if request.form.get("admin") == ADMIN and check_password_hash(
            HPSW, request.form.get("psw")
        ):
            login_admin()
            return redirect(url_for(".user", user=0))

        flash("invalid admin/password")
        return redirect(url_for(".login"))

    return render_template("login/log_admin.html")


@admin.route("/logout")
def logout():
    if is_logged():
        logout_admin()
    return redirect(url_for(".login"))


# POST user_id + exp_date + active
@admin.route("/user/<int:user>", methods=["GET", "POST"])
@login_req
def user(user):
    if request.method == "POST":
        user_id = request.form.get("user_id")
        crud.edit_user(user_id, request.form)
    if user == 0:
        user = {"id": 0, "exp_date": 0, "active": 0}
    else:
        user = crud.get_user(user)
    users = crud.get_user_all()
    return render_template("admin/a_user.html", u=user, users=users)


# POST email
@admin.route("/user/del", methods=["POST"])
@login_req
def user_del():
    user_email = request.form.get("email")
    crud.del_user(user_email)
    return redirect(url_for(".user", user=0))


# POST name + type
@admin.route("/pflist", methods=["GET", "POST"])
@login_req
def pf_list():
    if request.method == "POST":
        name = request.form.get("name")
        type = request.form.get("type")
        crud.add_prompt_field_list(name, type)

    pf_list = crud.get_prompt_field_list_all()
    return render_template("admin/a_pf_list.html", pf_list=pf_list)


# POST name
@admin.route("/pflist/del", methods=["POST"])
@login_req
def pf_list_del():
    name = request.form.get("name")
    crud.del_prompt_field_list(name)
    return redirect(url_for(".pf_list"))


# GET prompt_id, limit + page
@admin.route("/content/<user_id>")
@login_req
def content(user_id):
    content = crud.get_content_all(user_id, request.args)
    return render_template(
        "admin/a_content.html", content=content["list"], user_id=user_id
    )


# GET limit + page
@admin.route("/prompt/<int:user_id>")
@login_req
def prompt(user_id):
    prompt = crud.get_prompt_all(user_id, request.args)
    pfield_dict = {i["id"]: crud.get_prompt_field_all(i["id"]) for i in prompt["list"]}
    return render_template(
        "admin/a_prompt.html",
        prompt=prompt["list"],
        pfield_dict=pfield_dict,
        user_id=user_id,
    )


# GET
@admin.route("/iprompt/<int:user_id>")
@login_req
def iprompt(user_id):
    iprompt = crud.get_iprompt_all(user_id)
    return render_template("admin/a_iprompt.html", iprompt=iprompt, user_id=user_id)


# POST name(main, pfield, style, language) + value
@admin.route("/prmods", methods=["GET", "POST"])
@login_req
def prompt_mods():
    if request.method == "POST":
        name = request.form.get("name")
        value = request.form.get("value")
        crud.edit_prompt_mod(name, value)

    mods = crud.get_prompt_mod_all()
    return render_template("admin/a_pr_mods.html", mods=mods)
