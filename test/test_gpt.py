import json
from pprint import pprint

import pytest
from pytest import MonkeyPatch

from crud import crud
from gpt.prompt import Mods
from settings import TOPIC

prefix = "/api/user"
template = "test_template"
topic_list_str = "cat;dog;duck;humster"
topic_list = topic_list_str.split(";")
topic = "TopicList"
language = "Russian"
style = "modern"
mods = Mods()


@pytest.mark.skipif('config.getoption("--all") == "false"')
def test_active_user(app):
    "activate user id 1"
    with app.app_context():
        crud.edit_user(1, {"active": 1})


@pytest.mark.skipif('config.getoption("--all") == "false"')
def test_create_prompt(auth):
    auth.login()
    res = auth.client.post(
        prefix + "/prompt/0",
        data={
            "template": f"{template} {TOPIC}",
            "topic_list": topic_list_str,
            "params": json.dumps(
                {
                    "debug": False,
                    "tokens": 4000,
                    "list_order": "normal",
                    "language": language,
                    "style": style,
                    "longread": False,
                    "pro": True,
                    "html": True,
                }
            ),
        },
    )
    assert res.status_code == 201
    pytest.prompt_id = json.loads(res.data).get("prompt").get("id")


@pytest.mark.skipif('config.getoption("--all") == "false"')
def test_topic_list(monkeypatch: MonkeyPatch, auth):
    def fake_openai(user_id, prompt, tokens):
        assert user_id == 1
        assert prompt == (
            mods.topic.replace(TOPIC, topic)
            + mods.opts_base
            + mods.language.format(language)
            + mods.style.format(style)
        )
        assert tokens == 4000
        return prompt

    monkeypatch.setattr("gpt.creator.create_openai_completion", fake_openai)

    auth.login()
    auth.client.post(
        prefix + f"/content/get_topic/{pytest.prompt_id}",
        data={"topic": topic},
    )


@pytest.mark.skipif('config.getoption("--all") == "false"')
class TestShortread:
    @staticmethod
    def fake_openai(user_id, prompt, tokens):
        assert user_id == 1
        assert tokens == 4000
        return prompt

    def test_shortread_pro(self, monkeypatch: MonkeyPatch, auth):
        monkeypatch.setattr("gpt.creator.create_openai_completion", self.fake_openai)
        topic_ = topic_list.pop(0)

        auth.login()
        res = auth.client.post(prefix + f"/content/add_by/{pytest.prompt_id}")
        content_id = json.loads(res.data)["content_id"]

        res = auth.client.get(prefix + f"/content/{content_id}")
        data = json.loads(res.data)

        res = auth.client.get(prefix + f"/prompt/{pytest.prompt_id}")
        template_ = json.loads(res.data).get("template")

        assert data["prompt_id"] == pytest.prompt_id
        assert data["title"] == topic_
        assert (
            data["text"]
            == template_.replace(TOPIC, topic_)
            + mods.opts_base
            + mods.language.format(language)
            + mods.style.format(style)
            + mods.html
        )

    def test_shortread(self, monkeypatch: MonkeyPatch, auth):
        monkeypatch.setattr("gpt.creator.create_openai_completion", self.fake_openai)
        topic_ = topic_list.pop(0)

        auth.login()
        res = auth.client.post(
            prefix + f"/prompt/{pytest.prompt_id}",
            data={
                "params": json.dumps(
                    {
                        "debug": False,
                        "tokens": 4000,
                        "list_order": "normal",
                        "language": language,
                        "style": style,
                        "longread": False,
                        "pro": False,
                        "html": True,
                    }
                )
            },
        )
        assert res.status_code == 201

        res = auth.client.post(prefix + f"/content/add_by/{pytest.prompt_id}")
        content_id = json.loads(res.data)["content_id"]

        res = auth.client.get(prefix + f"/content/{content_id}")
        data = json.loads(res.data)

        assert data["prompt_id"] == pytest.prompt_id
        assert data["title"] == topic_
        assert (
            data["text"]
            == mods.article.replace(TOPIC, topic_)
            + mods.opts_base
            + mods.language.format(language)
            + mods.style.format(style)
            + mods.html
        )


@pytest.mark.skipif('config.getoption("--all") == "false"')
def test_longread(monkeypatch: MonkeyPatch, auth):
    toc = "1. First chapter\n2. Second chapter"
    topic_ = topic_list.pop(0)

    def fake_openai(user_id, prompt, tokens):
        assert user_id == 1
        assert tokens == 4000
        if mods.table[:10] in prompt:
            assert prompt == (
                mods.table.replace(TOPIC, topic_)
                + mods.opts_base
                + mods.language.format(language)
                + mods.style.format(style)
            )
            return toc
        assert prompt == (
            mods.table_fields.format(toc)
            + mods.opts_base
            + mods.language.format(language)
            + mods.style.format(style)
        )
        return "##field1 one\n##field2 two"

    async def fake_openai_async(user_id, prompt, tokens):
        return prompt

    monkeypatch.setattr("gpt.creator.create_openai_completion", fake_openai)
    monkeypatch.setattr("gpt.creator.create_openai_completion_async", fake_openai_async)

    auth.login()
    res = auth.client.post(
        prefix + f"/prompt/{pytest.prompt_id}",
        data={
            "params": json.dumps(
                {
                    "debug": False,
                    "tokens": 4000,
                    "list_order": "normal",
                    "language": language,
                    "style": style,
                    "longread": True,
                    "pro": False,
                    "html": True,
                }
            )
        },
    )
    assert res.status_code == 201

    res = auth.client.post(prefix + f"/content/add_by/{pytest.prompt_id}")
    content_id = json.loads(res.data)["content_id"]

    res = auth.client.get(prefix + f"/content/{content_id}")
    data = json.loads(res.data)

    assert data["prompt_id"] == pytest.prompt_id
    assert data["title"] == topic_

    pprint(data)
