import random

from crud import crud
from gpt.prompt import Prompt
from settings import TOPIC


class Constructor:
    def __init__(self, pt: Prompt) -> None:
        self.pt = pt

    def _use_topic_list(self):
        "pop topic from topic_list to template"

        def pop_item(lst: list, order: str) -> str:
            "pop item from list by order [reverse | random | normal]"
            item = "nothing"
            if lst:
                match order:
                    case "reverse":
                        item = lst.pop()
                    case "random":
                        item = lst.pop(random.randrange(len(lst)))
                    case _:
                        item = lst.pop(0)
            return item

        if self.pt.topic_list and TOPIC in self.pt.template:
            self.pt.topic_list = [i.strip() for i in self.pt.topic_list.split(";")]
            self.pt.topic = pop_item(
                self.pt.topic_list, self.pt.params.list_order
            ).strip()
            self.pt.template = self.pt.template.replace(TOPIC, self.pt.topic)

    def _use_seo_kw(self):
        "add keywords to template if 'seo'"
        if self.pt.params.seo and self.pt.kw_list:
            self.pt.template += self.pt.mods.seo.format(self.pt.kw_list)

    def _use_options(self, html=False):
        "add options to template: language, style, html-markup(if html=True)"
        opts = self.pt.mods.opts_base
        if self.pt.params.language:
            opts += self.pt.mods.language.format(self.pt.params.language)
        if self.pt.params.style:
            opts += self.pt.mods.style.format(self.pt.params.style)
        if html and self.pt.params.html:
            opts += self.pt.mods.html
        if opts != self.pt.mods.opts_base:
            self.pt.template += opts

    def _use_prompt_fields(self):
        "add prompt fields to template"
        pfield = crud.get_prompt_field_all(self.pt.id)
        for i in pfield:
            self.pt.template += self.pt.mods.add_field.format(i["name"])


class TopicListTemplateConstructor(Constructor):
    def make_topic_list(self, topic):
        "template constructor"
        self.pt.template = self.pt.mods.topic
        self.pt.template = self.pt.template.replace(TOPIC, topic)
        self._use_options()


class ShortreadTemplateConstructor(Constructor):
    def make_shortread(self):
        "template constructor"
        if not self.pt.params.pro:
            self.pt.template = self.pt.mods.article
        self._use_topic_list()
        self._use_seo_kw()
        self._use_options(html=True)

    def make_shortread_fields(self):
        """template constructor uses self.text"""
        self.pt.template = self.pt.mods.article_fields.format(self.pt.text)
        self._use_prompt_fields()
        self._use_options()


class LongreadTemplateConstructor(Constructor):
    def make_longread_table(self):
        "template constructor"
        self.pt.template = self.pt.mods.table
        self._use_topic_list()
        self._use_options()

    def make_longread_chapter(self, chapter_title) -> str:
        """template constructor uses self.toc\n
        return self.template for use in async func"""
        self.pt.template = self.pt.mods.chapter.format(self.pt.toc, chapter_title)
        self._use_seo_kw()
        self._use_options(html=True)
        return self.pt.template

    def make_longread_fields(self):
        """template constructor uses self.toc"""
        self.pt.template = self.pt.mods.table_fields.format(self.pt.toc)
        self._use_prompt_fields()
        self._use_options()
