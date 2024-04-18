from random import randint
from time import time

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property

from settings import TOPIC, TRIAL

db = SQLAlchemy()  # .Integer .String(size) .Text .DateTime .Float .Boolean .LargeBinary
"SQLAlchemy instance from models.py"


class User(db.Model):
    __tablename__ = "user"
    _protected = ["email", "psw", "reg_date"]

    __id = db.Column("id", db.Integer, primary_key=True, index=True)
    email = db.Column(db.String(50), unique=True, nullable=True, index=True)
    psw = db.Column(db.String(500), nullable=True)
    reg_date = db.Column(db.BigInteger, default=int(time()))
    exp_date = db.Column(
        db.BigInteger, nullable=True, default=int(time()) + 3600 * 24 * 365 * 30
    )
    active = db.Column(db.Boolean, nullable=True, default=0)
    tokens = db.Column(db.Integer, nullable=True, default=TRIAL)

    @hybrid_property
    def id(self):  # alternative to _protected = ['id']
        return self.__id

    def as_dict(self):
        "exclude 'psw'"
        return {
            i.name: getattr(self, i.name)
            for i in self.__table__.columns
            if i.name != "psw"
        }


class Prompt(db.Model):
    __tablename__ = "prompt"
    _protected = ["id", "user_id"]

    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name = db.Column(
        db.String(500), nullable=True, default=f"prompt_name#{randint(11, 99)}"
    )
    template = db.Column(db.Text, default=f"tell me about {TOPIC}")
    topic_list = db.Column(db.Text)
    kw_list = db.Column(db.Text)
    post = db.Column(db.String(50), default="false")
    params = db.Column(db.Text)

    def as_dict(self):
        return {i.name: getattr(self, i.name) for i in self.__table__.columns}


class PField(db.Model):
    __tablename__ = "p_field"
    _protected = ["id", "prompt_id"]

    id = db.Column(db.Integer, primary_key=True)
    prompt_id = db.Column(
        db.Integer,
        db.ForeignKey("prompt.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name = db.Column(
        db.String(500),
        db.ForeignKey("pf_list.name", ondelete="NO ACTION"),
        nullable=True,
    )
    type = db.Column(db.String(100))
    value = db.Column(db.Text)  # not used

    def as_dict(self):
        return {i.name: getattr(self, i.name) for i in self.__table__.columns}


class PFList(db.Model):
    __tablename__ = "pf_list"
    name = db.Column(db.String(500), primary_key=True)
    type = db.Column(db.String(100), nullable=True)

    def as_dict(self):
        return {i.name: getattr(self, i.name) for i in self.__table__.columns}


class Timetable(db.Model):
    __tablename__ = "timetable"
    _protected = ["id", "prompt_id"]

    id = db.Column(db.Integer, primary_key=True, index=True)
    prompt_id = db.Column(
        db.Integer,
        db.ForeignKey("prompt.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    day_utc = db.Column(db.Integer, default=0)
    hour_utc = db.Column(db.Integer, default=0)
    day = db.Column(db.Integer, default=0)
    hour = db.Column(
        db.Integer, db.CheckConstraint('"hour" BETWEEN 0 AND 23'), default=0
    )
    minute = db.Column(
        db.Integer, db.CheckConstraint('"minute" BETWEEN 0 AND 59'), default=0
    )
    timezone = db.Column(
        db.Integer, db.CheckConstraint('"timezone" BETWEEN -12 AND 12'), default=0
    )

    def as_dict(self):
        return {i.name: getattr(self, i.name) for i in self.__table__.columns}


class Content(db.Model):
    __tablename__ = "content"
    _protected = ["id", "user_id", "prompt_id"]

    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    prompt_id = db.Column(db.Integer, default=0, index=True)
    title = db.Column(db.Text)
    text = db.Column(db.Text)
    date = db.Column(db.Text)
    post = db.Column(db.String(50), nullable=True, default=False, index=True)

    def as_dict(self):
        return {i.name: getattr(self, i.name) for i in self.__table__.columns}


class CField(db.Model):
    __tablename__ = "c_field"
    _protected = ["id", "content_id"]

    id = db.Column(db.Integer, primary_key=True)
    content_id = db.Column(
        db.Integer,
        db.ForeignKey("content.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name = db.Column(db.Text)
    value = db.Column(db.Text)

    def as_dict(self):
        return {i.name: getattr(self, i.name) for i in self.__table__.columns}


class IPrompt(db.Model):
    __tablename__ = "i_prompt"
    _protected = ["id", "user_id"]

    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name = db.Column(db.String(500), nullable=True, default="new img prompt")
    size = db.Column(
        db.Integer,
        db.CheckConstraint('"size" IN (256, 512, 1024)'),
        nullable=True,
        default=256,
    )
    number = db.Column(
        db.Integer,
        db.CheckConstraint('"number" BETWEEN 1 AND 9'),
        nullable=True,
        default=1,
    )
    main = db.Column(db.Text)
    style = db.Column(db.Text)
    mod1 = db.Column(db.Text)
    mod2 = db.Column(db.Text)
    mod3 = db.Column(db.Text)
    mod4 = db.Column(db.Text)
    mod5 = db.Column(db.Text)

    def as_dict(self):
        return {i.name: getattr(self, i.name) for i in self.__table__.columns}


class PMod(db.Model):
    __tablename__ = "p_mod"
    _protected = ["name"]

    name = db.Column(db.String(100), nullable=True, primary_key=True)
    value = db.Column(db.Text)
    default = db.Column(db.Text)
    note = db.Column(db.Text)

    def as_dict(self):
        return {i.name: getattr(self, i.name) for i in self.__table__.columns}


# alternative with dataclass:

# from dataclasses import dataclass

# @dataclass            # adds methods: repr, asdict, astuple
# class User(db.Model):
#     __tablename__ = 'user'
#     __allow_unmapped__ = True
#     id:int
#     email:str
#     psw:str
#     reg_date:int
#     exp_date:int
#     active:int
