from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from loguru import logger
from werkzeug.security import check_password_hash, generate_password_hash

from crud import crud
from dalle_gen import dalle_gen
from gpt import gpt_gen
from userlogin import UserLogin
from utils import valid_psw

logger = logger.bind(name="views.user")
user = Blueprint("user", __name__, url_prefix="/views/user")


# GET
@user.route("/")
def index():
    return render_template("login/log_user.html")


# POST email + psw + psw2
@user.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        val_psw = valid_psw(request.form.get("psw"))
        if not val_psw[0]:
            flash(f"invalid character! allowed: {val_psw[1]}")
            return redirect(url_for(".register"))

        if request.form.get("psw") != request.form.get("psw2"):
            flash("passwords not match")
            return redirect(url_for(".register"))

        hpsw = generate_password_hash(request.form.get("psw"))
        res = crud.register(request.form.get("email"), hpsw)
        if res:
            crud.add_prompt(res.id)
            return redirect(url_for(".login"))

        flash("user exists")
    return render_template("login/reg_user.html")


# POST email + psw + ?remember
@user.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(".content"))

    if request.method == "POST":
        val_psw = valid_psw(request.form.get("psw"))
        if not val_psw[0]:
            flash("invalid character!")
            flash(f"allowed: {val_psw[1]}")
            return redirect(url_for(".login"))

        user = crud.login(request.form.get("email"))
        if user and check_password_hash(user.psw, request.form.get("psw")):
            userlogin = UserLogin().create(user)
            rm = True if request.form.get("remember") else False
            login_user(userlogin, remember=rm)
            return redirect(request.args.get("next") or url_for(".content"))

        flash("invalid username/password")
    return render_template("login/log_user.html")


# GET
@user.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for(".login"))


# GET
@user.route("/prompt")
@login_required
def prompt():
    prompt = crud.get_prompt_all(current_user.get_id(), request.args)
    pfield_dict = {i["id"]: crud.get_prompt_field_all(i["id"]) for i in prompt["list"]}
    timetable_dict = {i["id"]: crud.get_timetable_all(i["id"]) for i in prompt["list"]}
    return render_template(
        "user/prompt.html",
        prompt=prompt["list"],
        pfield=pfield_dict,
        timetable=timetable_dict,
    )


# POST /prompt_id: name, template, topic_list(a;b;..), kw_list, post, params
@user.route("/prompt/<int:prompt_id>", methods=["GET", "POST"])
def prompt_edit(prompt_id):
    if request.method == "POST":
        crud.edit_prompt(current_user.get_id(), prompt_id, request.form)

    prompt = crud.get_prompt(current_user.get_id(), prompt_id)
    pfield = crud.get_prompt_field_all(prompt_id)
    timetable = crud.get_timetable_all(prompt_id)
    return render_template(
        "user/prompt_edit.html", prompt=prompt, pfield=pfield, timetable=timetable
    )


# POST None
@user.route("/prompt/add", methods=["POST"])
def prompt_add():
    crud.add_prompt(current_user.get_id())
    return redirect(url_for(".prompt"))


# POST prompt_id
@user.route("/prompt/del", methods=["POST"])
def prompt_del():
    crud.del_prompt(current_user.get_id(), request.form.get("prompt_id"))
    return redirect(url_for(".prompt"))


# POST /prompt_id: name + value
@user.route("/pfield/<int:prompt_id>", methods=["GET", "POST"])
@login_required
def prompt_field(prompt_id):
    if request.method == "POST":
        name = request.form.get("name")
        value = request.form.get("value")
        crud.add_prompt_field(prompt_id, name, value)

    pfield = crud.get_prompt_field_all(prompt_id)
    pf_list = crud.get_prompt_field_list_all()
    return render_template(
        "user/pfield.html", pfield=pfield, prompt_id=prompt_id, pf_list=pf_list
    )


# POST prompt_id + pfield_id
@user.route("/pfield/del", methods=["POST"])
@login_required
def prompt_field_del():
    crud.del_prompt_field(request.form.get("prompt_id"), request.form.get("pfield_id"))
    return redirect(url_for(".prompt_field", prompt_id=request.form.get("prompt_id")))


# POST day + hour + minute + timezone
@user.route("/timetable/<int:prompt_id>", methods=["GET", "POST"])
@login_required
def timetable(prompt_id):
    if request.method == "POST":
        crud.add_timetable(
            prompt_id,
            request.form.get("day"),
            request.form.get("hour"),
            request.form.get("minute"),
            request.form.get("timezone"),
        )

    timetable = crud.get_timetable_all(prompt_id)
    return render_template(
        "user/timetable.html", timetable=timetable, prompt_id=prompt_id
    )


# POST prompt_id + timetable_id
@user.route("/timetable/del", methods=["POST"])
@login_required
def timetable_del():
    prompt_id = request.form.get("prompt_id")
    crud.del_timetable(prompt_id, request.form.get("timetable_id"))
    return redirect(url_for(".timetable", prompt_id=prompt_id))


@user.route("/content")
@login_required
def content():
    content = crud.get_content_all(current_user.get_id(), request.args)
    cfield_dict = {
        i["id"]: crud.get_content_field_all(i["id"]) for i in content["list"]
    }
    return render_template(
        "user/content.html", content=content["list"], cfield_dict=cfield_dict
    )


# POST title, text, post; <content_id> = 0(manual add) / int(edit)
@user.route("/content/<int:content_id>", methods=["GET", "POST"])
@login_required
def content_edit(content_id):
    if request.method == "POST":
        title = request.form.get("title")
        text = request.form.get("text")
        post = request.form.get("post")
        if content_id > 0:
            crud.edit_content(current_user.get_id(), content_id, request.form)
        else:
            crud.add_content(current_user.get_id(), title=title, text=text, post=post)
        return redirect(url_for(".content"))

    content = crud.get_content(current_user.get_id(), content_id)
    iprompt = crud.get_iprompt_all(current_user.get_id())
    cfield = crud.get_content_field_all(content_id)
    return render_template(
        "user/content_edit.html", content=content, iprompt=iprompt, cfield=cfield
    )


# POST None #[ ] gpt_gen
@user.route("/content/get_topic/", methods=["POST"])
@login_required
def content_get_topic():
    topic = request.form.get("topic", "")
    if len(topic) < 3:
        return render_template("user/topic_list.html", topic_list=[])

    try:
        res = gpt_gen(current_user.get_id(), request.form.get("prompt_id"), topic=topic)
        return render_template("user/topic_list.html", topic_list=res)

    except Exception as e:
        logger.exception(e)
        flash(f"error gpt_gen.py: {e}")
        return render_template("user/topic_list.html")


# POST prompt_id #[ ] gpt_gen
@user.route("/content/add", methods=["GET", "POST"])
@login_required
def content_add():
    if request.method == "POST":
        try:
            gpt_gen(current_user.get_id(), request.form.get("prompt_id"))

        except Exception as e:
            logger.exception(e)
            flash(f"error gpt_gen.py: {e}")
        return redirect(url_for(".content"))

    return render_template("user/item_add.html")


# POST content_id
@user.route("/content/del", methods=["POST"])
@login_required
def content_del():
    content_id = request.form.get("content_id")
    crud.del_content(current_user.get_id(), content_id)
    return redirect(url_for(".content"))


# GET
@user.route("/iprompt")
@login_required
def iprompt():
    iprompt = crud.get_iprompt_all(current_user.get_id())
    return render_template("user/iprompt.html", iprompt=iprompt)


# POST /iprompt_id: name, size, number, main, style, mod1..mod5
@user.route("/iprompt/<int:iprompt_id>", methods=["GET", "POST"])
def iprompt_edit(iprompt_id):
    if request.method == "POST":
        crud.edit_iprompt(current_user.get_id(), iprompt_id, request.form)
    iprompt = crud.get_iprompt(current_user.get_id(), iprompt_id)
    return render_template("user/iprompt_edit.html", iprompt=iprompt)


# POST None
@user.route("/iprompt/add", methods=["POST"])
def iprompt_add():
    crud.add_iprompt(current_user.get_id())
    return redirect(url_for(".iprompt"))


# POST iprompt_id
@user.route("/iprompt/del", methods=["POST"])
def iprompt_del():
    crud.del_iprompt(current_user.get_id(), request.form.get("iprompt_id"))
    return redirect(url_for(".iprompt"))


# POST content_id + iprompt_id #[ ] dalle_gen
@user.route("/images/add", methods=["POST"])
@login_required
def images_add():
    try:
        dalle_gen(
            current_user.get_id(),
            request.form.get("content_id"),
            request.form.get("iprompt_id"),
        )
    except Exception as e:
        logger.exception(e)
        flash(f"error dalle_gen.py: {e}")
    return redirect(url_for(".content"))
