import json

import pytest
from flask_login import current_user
from pytest import MonkeyPatch

from crud import DatabaseException

# from pprint import pprint


prefix = "/api/user"


@pytest.mark.skipif('config.getoption("--all") == "false"')
def test_register(client):
    response = client.post(
        prefix + "/register",
        data={"email": "test", "psw": "testpsw", "psw2": "testpsw"},
    )
    assert response.status_code == 201

    response = client.post(
        prefix + "/register",
        data={"email": "test", "psw": "testpsw"},  # no psw2
    )
    assert response.status_code == 400


@pytest.mark.skipif('config.getoption("--all") == "false"')
class TestLoginLogout:
    def test_login(self, client, auth):
        assert client.get(prefix + "/login").status_code == 405
        response = auth.login()
        assert response.status_code == 200
        assert response.headers[2] == ("Set-Cookie", "user_id=1; Path=/")

    def test_logout(self, client, auth):
        auth.login()
        with client:
            client.get("/")
            assert current_user.get_id() == 1
            auth.logout()
            assert current_user.get_id() is None

    def test_reset_psw(self, monkeypatch: MonkeyPatch, client, app):
        def fake_send_email(email, msg):
            # print('\nEMAIL:', email, '\nMESSAGE:', msg)
            if "http" in msg:
                pytest.url_resetpsw = msg[msg.find("http") :]
            if "New password:" in msg:
                pytest.new_psw = msg.splitlines()[-1]
            return {}

        monkeypatch.setattr("api.api_user.send_email", fake_send_email)

        response = client.post(
            prefix + "/resetpsw",
            data={"email": "test"},
        )
        assert response.status_code == 200

        response = client.get(pytest.url_resetpsw + "bad token")
        assert response.status_code == 400

        response = client.get(pytest.url_resetpsw)
        assert response.status_code == 201
        # print(pytest.new_psw)

    def test_newpsw(self, auth):
        auth.login(password=pytest.new_psw)
        response = auth.client.post(
            prefix + "/newpsw", data={"psw": "bad psw", "newpsw": "testpsw"}
        )
        assert response.status_code == 400

        response = auth.client.post(
            prefix + "/newpsw", data={"psw": pytest.new_psw, "newpsw": "testpsw"}
        )
        assert response.status_code == 201

    def test_settings(self, auth):
        auth.login()
        res = auth.client.get(prefix + "/settings")
        assert res.status_code == 200

    def test_statistic(self, auth):
        auth.login()
        res = auth.client.get(prefix + "/statistic")
        assert res.status_code == 200

    def test_pflist(self, auth):
        auth.login()
        res = auth.client.get(prefix + "/pflist")
        assert res.status_code == 200


@pytest.mark.skipif('config.getoption("--all") == "false"')
class TestContent:
    def test_content_empty(self, auth):
        auth.login()
        response = auth.client.get(prefix + "/content")
        assert json.loads(response.data)["list"] == []

    def test_add_content(self, auth):
        auth.login()
        response = auth.client.post(
            prefix + "/content/0", data={"title": "testtitle", "text": "testtext"}
        )
        assert response.status_code == 201

    def test_content_get(self, auth):
        auth.login()
        response = auth.client.get(prefix + "/content")
        pytest.content_id = json.loads(response.data)["list"][0]["id"]
        assert json.loads(response.data)["list"][0]["title"] == "testtitle"
        assert json.loads(response.data)["list"][0]["text"] == "testtext"

    def test_content_del(self, auth):
        auth.login()
        response = auth.client.post(prefix + f"/content/{pytest.content_id}/del")
        assert response.status_code == 204

    def test_add_content_10(self, auth):
        "add content for test_pagination()"
        auth.login()
        for i in range(1, 11):
            auth.client.post(
                prefix + "/content/0",
                data={"title": f"testtitle{i}", "text": f"testtext{i}"},
            )
        response = auth.client.get(prefix + "/content/count")
        assert json.loads(response.data)["count"] == 10

    @pytest.mark.parametrize(
        "limit, page, total, current, len_, title",
        [
            (3, 2, 4, 2, 3, 7),
            (5, 2, 2, 2, 5, 5),
            (9, 2, 2, 2, 1, 1),
        ],
    )
    def test_pagination(self, auth, limit, page, total, current, len_, title):
        auth.login()
        response = auth.client.get(prefix + f"/content?limit={limit}&page={page}")
        res_data = json.loads(response.data)
        assert res_data["totalPage"] == total
        assert res_data["currentPage"] == current
        assert len(res_data["list"]) == len_
        assert res_data["list"][0]["title"] == "testtitle" + str(title)


@pytest.mark.skipif('config.getoption("--all") == "false"')
class TestPrompt:
    def test_prompt_get_edit(self, auth):
        auth.login()
        res = auth.client.get(prefix + "/prompt")
        assert res.status_code == 200
        assert json.loads(res.data).get("list")[0].get("id") == 1
        assert json.loads(res.data).get("list")[0].get("user_id") == 1

        res = auth.client.post(prefix + "/prompt/1", data={"template": "test_template"})
        assert res.status_code == 201

        res = auth.client.get(prefix + "/prompt/1")
        assert res.status_code == 200
        assert json.loads(res.data).get("template") == "test_template"
        assert json.loads(res.data).get("user_id") == 1

    def test_prompt_add_del(self, auth):
        auth.login()
        res = auth.client.post(prefix + "/prompt/0", data={"template": "test_template"})
        assert res.status_code == 201

        prompt_id = json.loads(res.data).get("prompt").get("id")
        res = auth.client.post(prefix + f"/prompt/{prompt_id}/del")
        assert res.status_code == 204

        with pytest.raises(DatabaseException):
            auth.client.post(prefix + f"/prompt/{prompt_id}/del")

    def test_prompt_field(self, auth):
        auth.login()
        res = auth.client.get(prefix + "/prompt/1/pfield")
        assert json.loads(res.data) == []

        with pytest.raises(DatabaseException):
            auth.client.post(
                prefix + "/prompt/1/pfield",
                data={"name": "wrong_name", "value": "anyvalue"},
            )

        res = auth.client.post(
            prefix + "/prompt/1/pfield", data={"name": "title", "value": "anyvalue"}
        )
        assert res.status_code == 201

        res = auth.client.get(prefix + "/prompt/1/pfield")
        assert json.loads(res.data)[0].get("type") == "text"

        pfield_id = json.loads(res.data)[0].get("id")
        res = auth.client.post(prefix + f"/prompt/1/pfield/{pfield_id}/del")
        assert res.status_code == 204


@pytest.mark.skipif('config.getoption("--all") == "false"')
class TestTimetable:
    def test_timetable(self, auth):
        auth.login()
        res = auth.client.get(prefix + "/prompt/1/timetable")
        assert res.status_code == 200
        assert json.loads(res.data) == []

        res = auth.client.post(
            prefix + "/prompt/1/timetable",
            data={"day": 3, "hour": 4, "minute": 20, "timezone": 5},
        )
        assert res.status_code == 201
        assert json.loads(res.data).get("timetable").get("day_utc") == 2
        assert json.loads(res.data).get("timetable").get("hour_utc") == 23

        pytest.timetable_id = json.loads(res.data).get("timetable").get("id")

    def test_timetable_del(self, auth):
        auth.login()
        res = auth.client.post(
            prefix + f"/prompt/1/timetable/{pytest.timetable_id}/del"
        )
        assert res.status_code == 204


@pytest.mark.skipif('config.getoption("--all") == "false"')
def test_del_cascade(auth):
    """delete prompt_id = 1 ==>
    ON DELETE CASCADE p_field and timetable"""
    prompt_id = 1
    auth.login()
    auth.client.post(
        prefix + f"/prompt/{prompt_id}/pfield",
        data={"name": "title", "value": "anyvalue"},
    )
    auth.client.post(
        prefix + f"/prompt/{prompt_id}/timetable",
        data={"day": 3, "hour": 4, "minute": 20, "timezone": 5},
    )
    res = auth.client.post(prefix + f"/prompt/{prompt_id}/del")
    assert res.status_code == 204

    res = auth.client.get(prefix + f"/prompt/{prompt_id}/pfield")
    assert json.loads(res.data) == []

    res = auth.client.get(prefix + f"/prompt/{prompt_id}/timetable")
    assert json.loads(res.data) == []
