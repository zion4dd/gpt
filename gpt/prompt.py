import inspect
import json
import re

# from dataclasses import field  # fields, InitVar, dataclass
from typing import Literal

from pydantic.dataclasses import Field, dataclass

import gpt.pr_str as pr
from crud import crud
from settings import DEBUG, TOPIC


@dataclass
class Params:
    "Prompt params"

    debug: bool = DEBUG
    tokens: int = 4096
    list_order: Literal["normal", "random", "reverse"] = "normal"
    language: str = ""
    style: str = ""
    longread: bool = False
    pro: bool = False
    html: bool = False
    seo: bool = False

    @classmethod
    def from_dict(cls, dict_kwargs):
        "create instance from dict. ignore extra arguments passed to a dataclass"
        return cls(
            **{
                k: v
                for k, v in dict_kwargs.items()
                if k in inspect.signature(cls).parameters
            }
        )

    def __post_init__(self):
        self.tokens = int(self.tokens)
        self.language = self.language.capitalize()


@dataclass
class Mods:
    "Mods to construct prompt"

    topic: str = pr.topic % (TOPIC)
    # shortread mods
    article: str = pr.article % (TOPIC)
    article_fields: str = pr.article_fields
    # longread mods
    table: str = pr.table % (TOPIC)
    chapter: str = pr.chapter
    table_fields: str = pr.table_fields
    seo: str = pr.seo
    opts_base: str = pr.opts_base
    language: str = pr.language
    style: str = pr.style
    html: str = pr.html
    add_field: str = pr.add_field

    notes: dict = Field(
        default_factory=lambda: {
            "topic": "Topic-list mod. Use tag %s to insert topic." % TOPIC,
            "article": "Shortread main mod (not pro). Use tag %s to insert topic."
            % TOPIC,
            "article_fields": "Shortread mod to add fields. {0} - article.",
            "table": "Longread TOC mod. Use tag %s to insert topic." % TOPIC,
            "chapter": "Longread chapter mod. {0} - TOC; {1} - section title.",
            "table_fields": "Longread mod to add fields. {0} - TOC",
            "seo": "Mod to use keywords. {0} - kw_list",
            "opts_base": "Options base mod",
            "language": "{0} - language",
            "style": "{0} - style",
            "html": "HTML option mod",
            "add_field": "{0} - field name",
        }
    )

    @classmethod
    def get_mods_from_db(cls):
        "get mods from db and create Mods instance"
        mods = {}
        dbmods: list[dict] = crud.get_prompt_mod_all()
        mods: dict = {
            mod["name"]: mod["value"]
            for mod in dbmods
            if mod["value"]
            and mod["name"]
            in inspect.signature(cls).parameters  # (f.name for f in fields(cls))
        }
        return cls(**mods)


@dataclass
class Prompt:
    id: int = None
    user_id: int = None
    name: str = "prompt_name"
    template: str = 'say: "your template is empty :/"'
    topic_list: str | None = ""
    kw_list: str | None = ""
    post: str = "false"
    params: str | Params = None

    mods: Mods = None
    topic: str = ""
    text: str = "Text text text text\ntext text text text."
    toc: str = "1. One\n2. Two\n3. Three\n4. Four"

    def __post_init__(self):
        self.params = Params.from_dict(json.loads(self.params or "{}"))
        self.mods = Mods.get_mods_from_db()

    def write_topic_list(self):
        "write topic_list to db"
        crud.edit_prompt(
            self.user_id, self.id, {"topic_list": "; ".join(self.topic_list)}
        )

    def get_toc_list(self, *, numbered=True) -> list[str]:
        "get TOC as list[str, str ...]"
        toc_list = []
        pattern = r"^\d{1,2}\.\s"
        lines = self.toc.splitlines()
        for line in lines:
            if re.match(pattern, line):
                if not numbered:
                    line = line[line.index(".") + 1 :].strip()
                toc_list.append(line)
                continue
            if toc_list:
                toc_list[-1] += "\n" + line
        return toc_list[:3] if DEBUG else toc_list
