# from pprint import pprint

import httpx
import pytest

from app import app
from settings import DB_PATH

assert (
    DB_PATH == "sqlite:///../dbstorage/test.db"
), "settings.py: dotenv.load_dotenv(override=True) set to False"


@pytest.mark.skipif('config.getoption("--all") == "false"')
def test_api_docs():
    with httpx.Client(app=app, base_url="http://test") as client:
        r = client.get("/api/docs")
        assert r.status_code == 200

        r = client.get("/api/user/login")
        assert r.status_code == 405

        r = client.post("/api/user/login", data={"email": "test", "psw": "testpsw"})
        assert r.status_code == 200

        r = client.get("/api/user/content")
        assert r.status_code == 200
        # pprint(r.json())
