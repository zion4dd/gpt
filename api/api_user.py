# 201 add/edit success; 204 No content; 400 bad request; 401 unauthorized;
# 405 method not allowed; # 506 internal configuration error;
from flask import Blueprint, jsonify, make_response, request
from flask_login import current_user, login_required, login_user, logout_user
from validators import email as valid_email
from werkzeug.security import check_password_hash, generate_password_hash

from crud import crud
from dalle_gen import dalle_gen
from gpt import gpt_gen
from settings import VALID_EMAIL, VALID_PSW, SECRET
from userlogin import UserLogin
from utils import random_chars, send_email, valid_psw

api_user = Blueprint("api_user", __name__, url_prefix="/api/user")


# POST email + psw + psw2
@api_user.route("/register", methods=["POST"])
def register():
    email = request.form.get("email")
    psw = request.form.get("psw")
    psw2 = request.form.get("psw2")
    if not all([email, psw, psw2]):
        return jsonify(message="expected: email/psw/psw2"), 400

    if VALID_EMAIL and not valid_email(email):
        return jsonify(message="email not valid!"), 400

    val_psw = valid_psw(psw)  # -> tuple(bool, symbols)
    if VALID_PSW and not val_psw[0]:
        return jsonify(message="psw not valid!", comment=val_psw[1]), 400

    if psw != psw2:
        return jsonify(message="psw not match psw2"), 400

    hpsw = generate_password_hash(psw)
    user = crud.register(email, hpsw)  # -> object
    if not user:
        return jsonify(message="email exists"), 409

    crud.add_prompt(user.id)  # add prompt 1
    return jsonify(message="register success", user_id=user.id), 201


# POST email + psw + ?remember
@api_user.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    psw = request.form.get("psw")
    rm = True if request.form.get("remember") else False
    if not all([email, psw]):
        return jsonify(message="expected: email&psw"), 400

    if VALID_EMAIL and not valid_email(email):
        return jsonify(message="email not valid!", success=False), 400

    val_psw = valid_psw(psw)  # -> tuple(bool, symbols)
    if VALID_PSW and not val_psw[0]:
        return jsonify(message="psw not valid!", comment=val_psw[1]), 400

    user = crud.login(email)  # -> object
    if user and check_password_hash(user.psw, psw):
        userlogin = UserLogin().create(user)
        login_user(userlogin, remember=rm)
        response = make_response({"message": "login success", "success": True}, 200)
        response.set_cookie("user_id", str(current_user.get_id()))
        return response

    return jsonify(message="invalid email/password", success=False), 401


# POST email
@api_user.route("/resetpsw", methods=["GET", "POST"])
def reset_psw():
    if request.method == "POST":
        email = request.form.get("email")
    elif request.method == "GET":
        email = request.args.get("email")
    user = crud.login(email)
    if not user:
        return jsonify(message="email not exists", email=email), 400

    token = generate_password_hash(SECRET)

    if request.method == "POST":
        url = f"{request.url}?email={email}&token={token}"
        msg = f"""You are trying to reset your password.\n\nTo reset your password follow the link:\n{url}"""
        # http://localhost:5000/api/user/resetpsw?email=user@gmail.com&token=7e545af9f650
        res = send_email(email, msg)
        sent_to = "user" if res == {} else "admin"
        return jsonify(message="success", sent_to=sent_to, err=str(res))

    # if GET method: this block works by a link from users email -> str
    arg_token = request.args.get("token")
    if not check_password_hash(arg_token, SECRET):
        return "FAIL! Cant reset password. Error: bad token.", 400

    new_psw = random_chars()
    new_hpsw = generate_password_hash(new_psw)
    message = f"""You reset your password.\n\nNew password:\n{new_psw}"""
    res = send_email(email, message)
    if res == {}:
        msg = "Success!</br>New password sent to your email:</br>" + email
    else:
        msg = "Email error!</br>Please contact administrator.</br>" + str(res)
    crud.edit_user_psw(email, new_hpsw)
    return msg, 201


# POST psw + newpsw
@api_user.route("/newpsw", methods=["POST"])
@login_required
def new_psw():
    user = crud.get_user(current_user.get_id())
    if check_password_hash(user.psw, request.form.get("psw", "")):
        hpsw = generate_password_hash(request.form.get("newpsw", ""))
        res = crud.edit_user_psw(user.email, hpsw)
        return jsonify(message="password changed", success=True, user=res), 201

    return jsonify(message="bad psw", success=False), 400


# GET
@api_user.route("/logout")
@login_required
def logout():
    logout_user()
    response = make_response({"message": "user logout"})
    response.delete_cookie("user_id")
    return response


# GET
@api_user.route("/settings")
@login_required
def settings():
    return jsonify(current_user.get_data())


# GET
@api_user.route("/statistic")
@login_required
def statistic():
    res = crud.statistic(current_user.get_id())
    return jsonify(res)


# GET
@api_user.route("/pflist")
@login_required
def pf_list():
    res = crud.get_prompt_field_list_all()
    return jsonify(res)


# GET limit + page
@api_user.route("/prompt")
@login_required
def prompt():
    res = crud.get_prompt_all(current_user.get_id(), request.args)
    return jsonify(res)


# POST name, template, topic_list(a;b;..), kw_list, post(false|{date}), params
@api_user.route("/prompt/<int:prompt_id>", methods=["GET", "POST"])
@login_required
def prompt_edit(prompt_id):
    if request.method == "POST":
        if prompt_id == 0:
            res = crud.add_prompt(current_user.get_id())
            prompt_id = res.get("id")
        res = crud.edit_prompt(current_user.get_id(), prompt_id, request.form)
        return jsonify(message="success", prompt=res), 201

    res = crud.get_prompt(current_user.get_id(), prompt_id)
    return jsonify(res)


# POST None
@api_user.route("/prompt/<int:prompt_id>/del", methods=["POST"])
@login_required
def prompt_del(prompt_id):
    crud.del_prompt(current_user.get_id(), prompt_id)
    return jsonify(), 204


# POST name + value
@api_user.route("/prompt/<int:prompt_id>/pfield", methods=["GET", "POST"])
@login_required
def prompt_field(prompt_id):
    if request.method == "POST":
        res = crud.add_prompt_field(
            prompt_id, request.form.get("name"), request.form.get("value")
        )
        return jsonify(message="success", pfield=res), 201

    res = crud.get_prompt_field_all(prompt_id)
    return jsonify(res)


# POST None
@api_user.route("/prompt/<int:prompt_id>/pfield/<int:pfield_id>/del", methods=["POST"])
@login_required
def prompt_field_del(prompt_id, pfield_id):
    crud.del_prompt_field(prompt_id, pfield_id)
    return jsonify(), 204


# POST day + hour + minute + timezone
@api_user.route("/prompt/<int:prompt_id>/timetable", methods=["GET", "POST"])
@login_required
def timetable(prompt_id):
    if request.method == "POST":
        res = crud.add_timetable(
            prompt_id,
            day=request.form.get("day", 0),
            hour=request.form.get("hour", 0),
            minute=request.form.get("minute", 0),
            tz=request.form.get("timezone", 0),
        )
        return jsonify(message="success", timetable=res), 201

    res = crud.get_timetable_all(prompt_id)
    return jsonify(res)


# POST None
@api_user.route(
    "/prompt/<int:prompt_id>/timetable/<int:timetable_id>/del", methods=["POST"]
)
@login_required
def timetable_del(prompt_id, timetable_id):
    crud.del_timetable(prompt_id, timetable_id)
    return jsonify(), 204


# GET prompt_id, limit + page
@api_user.route("/content")
@login_required
def content():
    res = crud.get_content_all(current_user.get_id(), request.args)
    return jsonify(res)


# GET prompt_id
@api_user.route("/content/count")
@login_required
def content_count():
    res = crud.get_count(current_user.get_id(), request.args)
    return jsonify(res)


# POST title, text, post; <content_id> = [0(add) | int(edit)]
@api_user.route("/content/<int:content_id>", methods=["GET", "POST"])
@login_required
def content_edit(content_id):
    if request.method == "POST":
        if content_id == 0:
            res = crud.add_content(current_user.get_id())
            content_id = res.get("id")
        res = crud.edit_content(current_user.get_id(), content_id, request.form)
        return jsonify(message="success", content=res), 201

    res = crud.get_content(current_user.get_id(), content_id)
    return jsonify(res)


# POST None #[ ] gpt_gen
@api_user.route("/content/get_topic/<int:prompt_id>", methods=["POST"])
@login_required
def content_get_topic(prompt_id):
    topic = request.form.get("topic", "")
    if len(topic) < 3:
        return jsonify([])

    res = gpt_gen(current_user.get_id(), prompt_id, topic=topic)
    return jsonify(res)


# POST None #[ ] gpt_gen
@api_user.route("/content/add_by/<int:prompt_id>", methods=["POST"])
@login_required
def content_add(prompt_id):
    res = gpt_gen(current_user.get_id(), prompt_id)
    return jsonify(res), 201


# POST
@api_user.route("/content/<int:content_id>/del", methods=["POST"])
@login_required
def content_del(content_id):
    crud.del_content(current_user.get_id(), content_id)
    return jsonify(), 204


# GET
@api_user.route("/content/<int:content_id>/cfield")
@login_required
def cfield(content_id):
    res = crud.get_content_field_all(content_id)
    return jsonify(res)


# POST name, value
@api_user.route("/content/<int:content_id>/cfield/<int:cfield_id>", methods=["POST"])
@login_required
def cfield_edit(content_id, cfield_id):
    if cfield_id == 0:
        res = crud.add_content_field(content_id)
        cfield_id = res.get("id")
    res = crud.edit_content_field(content_id, cfield_id, request.form)
    return jsonify(message="success", cfield=res), 201


# POST None
@api_user.route(
    "/content/<int:content_id>/cfield/<int:cfield_id>/del", methods=["POST"]
)
@login_required
def cfield_del(content_id, cfield_id):
    crud.del_content_field(content_id, cfield_id)
    return jsonify(), 204


# GET
@api_user.route("/iprompt")
@login_required
def iprompt():
    res = crud.get_iprompt_all(current_user.get_id())
    return jsonify(res)


# POST name, size, number, main, style, mod1..mod5
@api_user.route("/iprompt/<int:iprompt_id>", methods=["GET", "POST"])
@login_required
def iprompt_edit(iprompt_id):
    if request.method == "POST":
        if iprompt_id == 0:
            res = crud.add_iprompt(current_user.get_id())
            iprompt_id = res.get("id")
        res = crud.edit_iprompt(current_user.get_id(), iprompt_id, request.form)
        return jsonify(message="success", iprompt=res), 201

    res = crud.get_iprompt(current_user.get_id(), iprompt_id)
    return jsonify(res)


# POST None
@api_user.route("/iprompt/<int:iprompt_id>/del", methods=["POST"])
@login_required
def iprompt_del(iprompt_id):
    crud.del_iprompt(current_user.get_id(), iprompt_id)
    return jsonify(), 204


# POST None #[ ] dalle_gen
@api_user.route(
    "/content/<int:content_id>/images/add_by/<int:iprompt_id>", methods=["POST"]
)
@login_required
def images_add(content_id, iprompt_id):
    res = dalle_gen(current_user.get_id(), content_id, iprompt_id)
    return jsonify(res), 201
