import inspect
from math import ceil
from time import time
from typing import Dict, List, Union

from flask_sqlalchemy import SQLAlchemy
from loguru import logger
from sqlalchemy import func

import models as m

logger = logger.bind(name="db")


class DatabaseException(Exception):
    pass


class CRUD:
    def __init__(self, db: SQLAlchemy):
        self.__db = db

    @property
    def db(self):
        "SQLAlchemy instance from models.py"
        return self.__db

    def _exc(self, e: Exception, rb: bool = False) -> None:
        "rb - db.session.rollback()"
        if rb:
            self.__db.session.rollback()
        logger.exception(e)
        msg = f"error db.py in {inspect.stack()[1][3]}: {str(e)}"
        raise DatabaseException(msg) from e

    # User
    def register(self, email, psw) -> Union[m.User, None]:
        try:
            res = m.User.query.filter_by(email=email).first()
            if res:
                return

            res = m.User(email=email, psw=psw)
            self.__db.session.add(res)
            self.__db.session.commit()
            return res

        except Exception as e:
            self._exc(e, rb=True)

    def login(self, email) -> m.User:
        try:
            res = m.User.query.filter_by(email=email).first()
            return res

        except Exception as e:
            self._exc(e)

    def get_user(self, user_id) -> m.User:
        # used_by gpt
        try:
            res = m.User.query.filter_by(id=user_id).first()
            return res

        except Exception as e:
            self._exc(e)

    def get_user_all(self) -> List[Dict]:
        try:
            res = m.User.query.all()
            return [i.as_dict() for i in res]

        except Exception as e:
            self._exc(e)

    def edit_user(self, user_id, attrs: dict) -> Dict:
        try:
            res = m.User.query.filter_by(id=user_id).first()
            if not res:
                raise ValueError("record not found in db")

            for k, v in attrs.items():
                if k in getattr(res, "_protected"):
                    raise AttributeError("protected attribute")

                if k in ("active", "tokens", "exp_date"):
                    v = int(v)
                if k == "tokens":
                    v += res.tokens
                if k == "exp_date" and v < 365 * 30:
                    v = (86400 * v) + int(max(res.exp_date, time()))
                setattr(res, k, v)
            self.__db.session.commit()
            return res.as_dict()

        except Exception as e:
            self._exc(e, rb=True)

    def edit_user_psw(self, email, hpsw) -> Dict:
        try:
            res = m.User.query.filter_by(email=email).first()
            if not res:
                raise ValueError("record not found in db")

            res.psw = hpsw
            self.__db.session.commit()
            return res.as_dict()

        except Exception as e:
            self._exc(e, rb=True)

    def del_user(self, email) -> None:
        try:
            res = m.User.query.filter_by(email=email).first()
            if not res:
                raise ValueError("record not found in db")

            self.__db.session.delete(res)
            self.__db.session.commit()

        except Exception as e:
            self._exc(e, rb=True)

    def statistic(self, user_id):
        "-> 'prompt_count', 'content_count: true, false, total'"
        try:
            p = m.Prompt.query.filter_by(user_id=user_id).count()
            c = (
                m.Content.query.with_entities(
                    m.Content.post, func.count(m.Content.post)
                )
                .group_by(m.Content.post)
                .all()
            )
            c = dict(c)
            c["total"] = sum(c.values())
            return {"prompt_count": p, "content_count": c}

        except Exception as e:
            self._exc(e, rb=True)

    # Prompt
    def get_prompt_all(self, user_id, filter) -> Dict:
        "-> Dict.keys: 'list', 'totalPage', 'currentPage'"
        lim = int(filter.get("limit", 100))
        current_page = int(filter.get("page", 1))
        offset = (current_page - 1) * lim
        try:
            res = (
                m.Prompt.query.filter_by(user_id=user_id)
                .order_by(m.Prompt.id.desc())
                .limit(lim)
                .offset(offset)
                .all()
            )  # all: limit < 0, offset <= 0
            count = m.Prompt.query.filter_by(user_id=user_id).count()
            total_page = ceil(count / lim) if count / lim > 1 else 1
            list_ = [i.as_dict() for i in res]
            return {"list": list_, "totalPage": total_page, "currentPage": current_page}

        except Exception as e:
            self._exc(e)

    def get_prompt(self, user_id, prompt_id) -> Dict:
        # used_by gpt
        try:
            res = m.Prompt.query.filter_by(user_id=user_id, id=prompt_id).first()
            if not res:
                raise ValueError("record not found in db")

            return res.as_dict()

        except Exception as e:
            self._exc(e)

    def edit_prompt(self, user_id, prompt_id, attrs: dict) -> Dict:
        # used_by gpt
        "sets prompt setting value by its name"
        try:
            res = m.Prompt.query.filter_by(user_id=user_id, id=prompt_id).first()
            if not res:
                raise ValueError("record not found in db")

            for k, v in attrs.items():
                if k in getattr(res, "_protected"):
                    raise AttributeError("protected attribute")

                setattr(res, k, v)
            self.__db.session.commit()
            return res.as_dict()

        except Exception as e:
            self._exc(e, rb=True)

    def add_prompt(self, user_id) -> Dict:
        try:
            res = m.Prompt(user_id=user_id)
            self.__db.session.add(res)
            self.__db.session.commit()
            return res.as_dict()

        except Exception as e:
            self._exc(e, rb=True)

    def del_prompt(self, user_id, prompt_id) -> None:
        try:
            res = m.Prompt.query.filter_by(user_id=user_id, id=prompt_id).first()
            if not res:
                raise ValueError("record not found in db")

            self.__db.session.delete(res)
            self.__db.session.commit()

        except Exception as e:
            self._exc(e, rb=True)

    # PField
    def get_prompt_field_all(self, prompt_id) -> List[Dict]:
        # used_by gpt
        "gets prompt fields: img, title, conclusion etc.."
        try:
            res = m.PField.query.filter_by(prompt_id=prompt_id).all()
            return [i.as_dict() for i in res]

        except Exception as e:
            self._exc(e)

    def add_prompt_field(self, prompt_id, name, value) -> Dict:
        "adds a prompt field with name from pf_list table"
        try:
            sub = m.PFList.query.filter_by(name=name).first()
            if not sub:
                raise ValueError("record not found in db")

            res = m.PField(
                prompt_id=prompt_id, name=sub.name, type=sub.type, value=value
            )
            self.__db.session.add(res)
            self.__db.session.commit()
            return res.as_dict()

        except Exception as e:
            self._exc(e, rb=True)

    def del_prompt_field(self, prompt_id, pfield_id) -> None:
        try:
            res = m.PField.query.filter_by(prompt_id=prompt_id, id=pfield_id).first()
            if not res:
                raise ValueError("record not found in db")

            self.__db.session.delete(res)
            self.__db.session.commit()

        except Exception as e:
            self._exc(e, rb=True)

    # PFList
    def get_prompt_field_list_all(self) -> List[Dict]:
        try:
            res = m.PFList.query.all()
            return [i.as_dict() for i in res]

        except Exception as e:
            self._exc(e)

    def add_prompt_field_list(self, name, type) -> Dict:
        try:
            res = m.PFList(name=name, type=type)
            self.__db.session.add(res)
            self.__db.session.commit()
            return res.as_dict()

        except Exception as e:
            self._exc(e, rb=True)

    def del_prompt_field_list(self, name) -> None:
        try:
            res = m.PFList.query.filter_by(name=name).first()
            if not res:
                raise ValueError("record not found in db")

            self.__db.session.delete(res)
            self.__db.session.commit()

        except Exception as e:
            self._exc(e, rb=True)

    # Timetable
    def get_timetable_all(self, prompt_id) -> List[Dict]:
        try:
            res = m.Timetable.query.filter_by(prompt_id=prompt_id).all()
            return [i.as_dict() for i in res]

        except Exception as e:
            self._exc(e)

    def add_timetable(self, prompt_id, day, hour, minute, tz) -> Dict:
        def time_convert(tz, d, h):
            "convert D-days('1357') and h-hours according to tz-timezone"
            h = int(h) - int(tz)
            if h < 0:
                d = "".join([str(int(i) - 1) for i in d if i.isdigit()]).replace(
                    "0", "7"
                )
                h += 24
            elif h > 23:
                d = "".join([str(int(i) + 1) for i in d if i.isdigit()]).replace(
                    "8", "1"
                )
                h -= 24
            return d, h

        du, hu = time_convert(tz, day, hour)  # day_utc, hour_utc
        try:
            res = m.Timetable(
                prompt_id=prompt_id,
                day_utc=du,
                hour_utc=hu,
                day=day,
                hour=hour,
                minute=minute,
                timezone=tz,
            )
            self.__db.session.add(res)
            self.__db.session.commit()
            return res.as_dict()

        except Exception as e:
            self._exc(e, rb=True)

    def del_timetable(self, prompt_id, timetable_id) -> None:
        try:
            res = m.Timetable.query.filter_by(
                prompt_id=prompt_id, id=timetable_id
            ).first()
            if not res:
                raise ValueError("record not found in db")

            self.__db.session.delete(res)
            self.__db.session.commit()

        except Exception as e:
            self._exc(e, rb=True)

    def get_event_all(self, day: int, hour: int, min: int) -> List[Dict]:
        # used_by gpt
        """get events from db 'timetable' for the given UTC day, hour, minute
        [{'user_id': int, 'prompt_id': int}, {}...]"""
        try:  # Prompt.id == Timetable.prompt_id
            res = (
                self.__db.session.query(m.Prompt, m.Timetable)
                .join(m.Timetable)
                .filter(
                    m.Timetable.day_utc.like(f"%{day}%"),
                    m.Timetable.hour_utc == hour,
                    m.Timetable.minute == min // 10 * 10,
                )
                .group_by(m.Prompt)
                .all()
            )
            events = []
            for i in res:
                events.append({"user_id": i.Prompt.user_id, "prompt_id": i.Prompt.id})
                print(
                    "queries: Prompt >>",
                    i.Prompt.as_dict(),
                    "\nqueries: Tmtb >>",
                    i.Timetable.as_dict(),
                    "\n------",
                )
            print("queries: Events >>", events)
            return events

        except Exception as e:
            self._exc(e)

    # Content
    def get_content_all(self, user_id, filter: dict) -> Dict:
        """filter dict: {'limit': 100, 'page': 1}
        -> Dict.keys: 'list', 'totalPage', 'currentPage'"""
        lim = int(filter.get("limit", 100))
        current_page = int(filter.get("page", 1))
        offset = (current_page - 1) * lim
        prompt_id = int(filter.get("prompt_id", 0))
        try:
            res = (
                m.Content.query.filter_by(user_id=user_id)
                .filter(True if prompt_id == 0 else m.Content.prompt_id == prompt_id)
                .order_by(m.Content.id.desc())
                .limit(lim)
                .offset(offset)
                .all()
            )  # all: limit < 0, offset <= 0
            count = (
                m.Content.query.filter_by(user_id=user_id)
                .filter(True if prompt_id == 0 else m.Content.prompt_id == prompt_id)
                .count()
            )
            total_page = ceil(count / lim) if count / lim > 1 else 1
            list_ = [i.as_dict() for i in res]
            return {"list": list_, "totalPage": total_page, "currentPage": current_page}

        except Exception as e:
            self._exc(e)

    def get_count(self, user_id, filter: dict) -> dict:
        """filter dict: {'prompt_id': 0}
        -> dict: {'count': 1}"""
        prompt_id = int(filter.get("prompt_id", 0))
        try:
            count = (
                m.Content.query.filter_by(user_id=user_id)
                .filter(True if prompt_id == 0 else m.Content.prompt_id == prompt_id)
                .count()
            )
            return {"count": count}

        except Exception as e:
            self._exc(e)

    def get_content(self, user_id, content_id) -> Dict:
        # used_by dalle
        try:
            res = m.Content.query.filter_by(user_id=user_id, id=content_id).first()
            if not res:
                raise ValueError("record not found in db")

            return res.as_dict()

        except Exception as e:
            self._exc(e)

    def edit_content(self, user_id, content_id, attrs: dict) -> Dict:
        try:
            res = m.Content.query.filter_by(user_id=user_id, id=content_id).first()
            if not res:
                raise ValueError("record not found in db")

            for k, v in attrs.items():
                if k in getattr(res, "_protected"):
                    raise AttributeError("protected attribute")

                setattr(res, k, v)
            self.__db.session.commit()
            return res.as_dict()

        except Exception as e:
            self._exc(e, rb=True)

    def add_content(
        self, user_id, prompt_id=0, title="title", text="text", post="false"
    ) -> Dict:
        # used_by gpt
        try:
            res = m.Content(
                user_id=user_id,
                prompt_id=prompt_id,
                title=title,
                text=text,
                date=int(time()),
                post=post,
            )
            self.__db.session.add(res)
            self.__db.session.commit()
            return res.as_dict()

        except Exception as e:
            self._exc(e, rb=True)

    def del_content(self, user_id, content_id) -> None:
        try:
            res = m.Content.query.filter_by(user_id=user_id, id=content_id).first()
            if not res:
                raise ValueError("record not found in db")

            self.__db.session.delete(res)
            self.__db.session.commit()

        except Exception as e:
            self._exc(e, rb=True)

    # CField
    def get_content_field_all(self, content_id) -> List[Dict]:
        # used_by gpt
        try:
            res = m.CField.query.filter_by(content_id=content_id).all()
            return [i.as_dict() for i in res]

        except Exception as e:
            self._exc(e)

    def add_content_field(self, content_id, name="name", value="value") -> Dict:
        # used_by gpt & dalle
        try:
            res = m.CField(content_id=content_id, name=name, value=value)
            self.__db.session.add(res)
            self.__db.session.commit()
            return res.as_dict()

        except Exception as e:
            self._exc(e, rb=True)

    def edit_content_field(self, content_id, cfield_id, attrs: dict) -> Dict:
        try:
            res = m.CField.query.filter_by(content_id=content_id, id=cfield_id).first()
            if not res:
                raise ValueError("record not found in db")

            for k, v in attrs.items():
                if k in getattr(res, "_protected"):
                    raise AttributeError("protected attribute")

                setattr(res, k, v)
            self.__db.session.commit()
            return res.as_dict()

        except Exception as e:
            self._exc(e, rb=True)

    def del_content_field(self, content_id, cfield_id) -> None:
        try:
            res = m.CField.query.filter_by(content_id=content_id, id=cfield_id).first()
            if not res:
                raise ValueError("record not found in db")
            self.__db.session.delete(res)
            self.__db.session.commit()

        except Exception as e:
            self._exc(e, rb=True)

    # CField images
    def get_images_count(self, content_id) -> int:
        # used_by dalle
        "counts the number of images of certain content"
        try:
            res = m.CField.query.filter(
                m.CField.content_id == content_id, m.CField.name.like("img")
            ).count()
            return res

        except Exception as e:
            self._exc(e)

    def get_images_all(self) -> list[str]:
        # used_by img_man
        "gets all images from CField table"
        try:
            res = m.CField.query.filter(m.CField.name.like("img")).all()
            return [i.value for i in res]

        except Exception as e:
            self._exc(e)

    # IPrompt
    def get_iprompt_all(self, user_id) -> List[Dict]:
        try:
            res = m.IPrompt.query.filter_by(user_id=user_id).all()
            return [i.as_dict() for i in res]

        except Exception as e:
            self._exc(e)

    def get_iprompt(self, user_id, iprompt_id) -> Dict:
        # used_by gpt
        try:
            res = m.IPrompt.query.filter_by(user_id=user_id, id=iprompt_id).first()
            if not res:
                raise ValueError("record not found in db")

            return res.as_dict()

        except Exception as e:
            self._exc(e)

    def edit_iprompt(self, user_id, iprompt_id, attrs: dict) -> Dict:
        # used_by gpt
        "sets prompt setting value by its name"
        try:
            res = m.IPrompt.query.filter_by(user_id=user_id, id=iprompt_id).first()
            if not res:
                raise ValueError("record not found in db")

            for k, v in attrs.items():
                if k in getattr(res, "_protected"):
                    raise AttributeError("protected attribute")

                setattr(res, k, v)
            self.__db.session.commit()
            return res.as_dict()

        except Exception as e:
            self._exc(e, rb=True)

    def add_iprompt(self, user_id) -> Dict:
        try:
            res = m.IPrompt(user_id=user_id)
            self.__db.session.add(res)
            self.__db.session.commit()
            return res.as_dict()

        except Exception as e:
            self._exc(e, rb=True)

    def del_iprompt(self, user_id, iprompt_id) -> None:
        try:
            res = m.IPrompt.query.filter_by(user_id=user_id, id=iprompt_id).first()
            if not res:
                raise ValueError("record not found in db")

            self.__db.session.delete(res)
            self.__db.session.commit()

        except Exception as e:
            self._exc(e, rb=True)

    # PMod
    def get_prompt_mod_all(self) -> List[Dict]:
        """get prompt modifiers from DB.
        -> [{"name": "mod_name", "value": "mod_value", "default": "mod_default", "note": "mod_note"}, {...}, ...]
        """
        try:
            res = m.PMod.query.all()
            return [i.as_dict() for i in res]

        except Exception as e:
            self._exc(e)

    def edit_prompt_mod(self, name, value, column="value") -> Dict:
        """column - column in p_mod table.
        default: 'value'. optional: default | note"""
        column = column if column else "value"
        try:
            res = m.PMod.query.filter_by(name=name).first()
            if not res:
                raise ValueError("record not found in db")

            if column in getattr(res, "_protected"):
                raise AttributeError("protected attribute")

            setattr(res, column, value)
            self.__db.session.commit()
            return res.as_dict()

        except Exception as e:
            self._exc(e, rb=True)


crud = CRUD(m.db)
"""DB instance with query methods from db.py"""
