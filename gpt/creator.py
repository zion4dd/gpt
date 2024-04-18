import asyncio
import re
from abc import ABC, abstractmethod
from time import sleep

from loguru import logger

from crud import crud
from gpt.constructor import (
    Constructor,
    LongreadTemplateConstructor,
    ShortreadTemplateConstructor,
    TopicListTemplateConstructor,
)
from gpt.openai import create_openai_completion, create_openai_completion_async

logger = logger.bind(name="gpt")


def strip_html(text: str, tag="body") -> str:
    "get text within tag"
    start = text.find("<%s>" % tag)
    end = text.find("</%s>" % tag)
    start = 0 if start == -1 else start + len(tag) + 2
    end = len(text) if end == -1 else end
    return text[start:end].strip()


def parse_mark(text: str) -> dict[str, str]:
    "parse text by mark: ##mark"
    pattern = "##[\w:-]+"  ##mark## pattern = "##(.*?)##"; match.group(1)
    result = {}
    for match in re.finditer(pattern, text):
        key = match.group(0)
        content_start = match.end()
        next_match = re.search(pattern, text[content_start:])
        content_end = (
            len(text) if next_match is None else next_match.start() + content_start
        )
        content = text[content_start:content_end]
        result[key.strip("#:-")] = content.strip(" \n'\";:.,")
    return result


class Creator(ABC):
    """abstactmethod:\n
    def __init__(self, constructor: Constructor)\n
    def create()"""

    @abstractmethod
    def __init__(self, constructor: Constructor) -> None:
        self.constructor = constructor

    @abstractmethod
    def create(self):
        logger.info(f"{type(self).__name__:=^50}")


class Mixin:
    """def write_to_db()\n
    def create_content_fields()"""

    constructor: Constructor

    def content_to_db(self, title="title", text="text", post="false") -> int:
        "add content to db"
        last_content = crud.add_content(
            user_id=self.constructor.pt.user_id,
            prompt_id=self.constructor.pt.id,
            title=title,
            text=text,
            post=post,
        )
        return last_content.get("id")

    def create_content_fields(self, content_id):
        "use create_openai_completion()"

        logger.info(f"=> Field_template:\n{self.constructor.pt.template}")
        fields_text = create_openai_completion(
            self.constructor.pt.user_id,
            self.constructor.pt.template,
            self.constructor.pt.params.tokens,
        )

        logger.info(f"=> Field_text:\n{fields_text}")
        fields_dict = parse_mark(fields_text)

        logger.info(f"=> Field_dict:\n{fields_dict}")
        for k, v in fields_dict.items():
            crud.add_content_field(content_id, k, v)


class TopicList(Creator):
    constructor: TopicListTemplateConstructor

    def __init__(self, constructor: TopicListTemplateConstructor, topic: str):
        self.constructor = constructor
        self.topic = topic

    def create(self) -> list[str]:
        super().create()
        self.constructor.make_topic_list(self.topic)
        if self.constructor.pt.params.debug:
            return [self.constructor.pt.template]

        logger.info(f"=> TEMPLATE TOPIC LIST:\n{self.constructor.pt.template}")
        logger.info("=> TOPIC LIST:")
        self.constructor.pt.toc = create_openai_completion(
            self.constructor.pt.user_id,
            self.constructor.pt.template,
            self.constructor.pt.params.tokens,
        )
        logger.debug(self.constructor.pt.toc)
        return self.constructor.pt.get_toc_list(numbered=False)


class Shortread(Mixin, Creator):
    constructor: ShortreadTemplateConstructor

    def __init__(self, constructor: ShortreadTemplateConstructor) -> None:
        self.constructor = constructor

    def create(self):
        super().create()
        self.constructor.make_shortread()
        if self.constructor.pt.params.debug:
            return self.debug_shortread()

        return self.shortread()

    def debug_shortread(self) -> dict:
        "write all shortread templates to DB content"
        text = self.constructor.pt.template
        self.constructor.make_shortread_fields()
        text += "\n\n===================\n\n" + self.constructor.pt.template
        last_content_id = self.content_to_db(title="DEBUG: gpt off", text=text)
        return {
            "message": "success",
            "content_id": last_content_id,
            "gpt": "off",
        }

    def shortread(self):
        self.create_article()
        last_content_id = self.content_to_db(
            title=self.constructor.pt.topic,
            text=self.constructor.pt.text,
            post=self.constructor.pt.post,
        )

        self.constructor.pt.write_topic_list()
        self.constructor.make_shortread_fields()
        self.create_content_fields(last_content_id)
        return {"message": "success", "content_id": last_content_id, "gpt": "on"}

    def create_article(self):
        logger.info(f"=> TEMPLATE:\n{self.constructor.pt.template}")
        logger.info("=> ARTICLE:")
        self.constructor.pt.text = create_openai_completion(
            self.constructor.pt.user_id,
            self.constructor.pt.template,
            self.constructor.pt.params.tokens,
        )
        self.strip_html()

    def strip_html(self):
        "strip html by <body> tag"
        if self.constructor.pt.params.html:
            self.constructor.pt.text = strip_html(self.constructor.pt.text)


class Longread(Mixin, Creator):
    constructor: LongreadTemplateConstructor

    def __init__(self, constructor: LongreadTemplateConstructor) -> None:
        self.constructor = constructor

    def create(self):
        super().create()
        self.constructor.make_longread_table()
        if self.constructor.pt.params.debug:
            return self.debug_longread()

        return self.longread()

    def debug_longread(self) -> dict:
        "write all longread templates to DB content"
        text = self.constructor.pt.template
        chapters = self.constructor.pt.get_toc_list()
        self.constructor.make_longread_chapter(chapters[0])
        text += "\n\n===================\n\n" + self.constructor.pt.template
        self.constructor.make_longread_fields()
        text += "\n\n===================\n\n" + self.constructor.pt.template
        last_content_id = self.content_to_db(title="DEBUG: gpt off", text=text)
        return {
            "message": "success",
            "content_id": last_content_id,
            "gpt": "off",
        }

    def longread(self) -> dict:
        self.create_toc()
        chapters_list: list[str] = asyncio.run(self.make_chapters())
        self.constructor.pt.text += "\n\n" + "\n\n".join(chapters_list)
        last_content_id = self.content_to_db(
            title=self.constructor.pt.topic,
            text=self.constructor.pt.text,
            post=self.constructor.pt.post,
        )

        self.constructor.pt.write_topic_list()
        self.constructor.make_longread_fields()
        self.create_content_fields(last_content_id)
        return {"message": "success", "content_id": last_content_id, "gpt": "on"}

    def create_toc(self):
        "create toc and put into pt.text"
        logger.info(f"=> TABLE TEMPLATE:\n{self.constructor.pt.template}")
        logger.info("=> TABLE:")
        self.constructor.pt.toc = create_openai_completion(
            self.constructor.pt.user_id,
            self.constructor.pt.template,
            self.constructor.pt.params.tokens,
        )
        logger.info(self.constructor.pt.toc)
        self.constructor.pt.text = self.constructor.pt.toc
        self.toc_to_html()

    def toc_to_html(self):
        "convert TOC to html"
        if self.constructor.pt.params.html:
            self.constructor.pt.text = (
                '<div class="table-of-conts">\n%s<br>\n</div>\n'
                % self.constructor.pt.toc.replace("\n", "<br>\n")
            )
            logger.debug(f"TEXT TABLE TO HTML:\n{self.constructor.pt.text}")

    async def make_one_chapter(self, ch_title: str) -> str:
        "create and return chapter"
        ch_template = self.constructor.make_longread_chapter(ch_title)  # use pt.toc
        logger.debug(f"=> CHAPTER TEMPLATE:\n{ch_template}")
        logger.info(f"=> CHAPTER {ch_title}:")
        for _ in range(3):  # attempts
            try:
                chapter = await create_openai_completion_async(
                    self.constructor.pt.user_id,
                    ch_template,
                    self.constructor.pt.params.tokens,
                )
                logger.info(chapter)
                if self.constructor.pt.params.html:
                    chapter = strip_html(chapter)
                    ch_title = "<h2>" + ch_title + "</h2>"
                break

            except Exception as e:
                chapter = "\_(o_O)_/ " + str(e)
                sleep(2)

        return ch_title + "\n\n" + chapter

    async def make_chapters(self) -> list[str]:
        "async create and return list with chapters"
        return await asyncio.gather(
            *[
                self.make_one_chapter(ch_title)
                for ch_title in self.constructor.pt.get_toc_list()
            ]
        )


# DEPRECATED

# def parse_tags(text: str) -> dict[str, str]:
#     "parse text by tags [>tag<]"
#     lst = text.split('[>')
#     result = {i.split('<]')[0].strip():                       # key
#               i.split('<]')[1].strip() for i in lst if i}     # value
#     return result


# def count_chapters(table: str) -> int:
#     "Counts the number of chapters in a table of contents string."
#     pattern = r'^\d{1,2}\.\s\b'
#     return len([1 for line in table.splitlines() if re.match(pattern, line)])
