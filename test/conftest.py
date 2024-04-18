# https://flask.palletsprojects.com/en/3.0.x/testing/#form-data
# https://flask.palletsprojects.com/en/3.0.x/tutorial/tests/#authentication
# pytest --cov --cov-report html --durations=3

import pytest
from sqlalchemy import text

from app import app as app_
from crud import crud
from settings import DB_PATH


def pytest_addoption(parser):
    parser.addoption("--all", default="false", choices=("true", "false"))


# add test user
sql_user = text(
    """
INSERT INTO User (email, psw) 
VALUES ('test', 'pbkdf2:sha256:260000$YqvN8ENR2O9Uthxy$8d088ca97cfd48f6bf9193984f46982256b2be5d505223489019dc8d48e81cf5');
"""
)  # psw: test

# fill table pf_list
sql_pflist = text(
    """
INSERT INTO pf_list (name, type)
VALUES ('title', 'text'), ('keywords', 'textarea');
"""
)


@pytest.fixture(scope="session")
def app():
    assert (
        DB_PATH == "sqlite:///../dbstorage/test.db"
    ), "settings.py: dotenv.load_dotenv(override=True) set to False"
    # assert DB_PATH == "postgresql://admin_gpt:123@localhost:5432/gpt_test"
    app_.testing = True  # exceptions to propagate to the test client

    with app_.app_context():
        crud.db.drop_all()
        crud.db.create_all()
        crud.db.session.execute(sql_pflist)
        crud.db.session.commit()

    yield app_


@pytest.fixture
def client(app):
    return app.test_client()  # creates HTTP request context


class ApiAuthActions(object):
    def __init__(self, client):
        self.client = client

    def login(self, username="test", password="testpsw"):
        return self.client.post(
            "/api/user/login", data={"email": username, "psw": password}
        )

    def logout(self):
        return self.client.get("/api/user/logout")


@pytest.fixture
def auth(client):
    return ApiAuthActions(client)
