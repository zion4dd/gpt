import pytest

from crud import crud


@pytest.mark.skipif('config.getoption("--all") == "false"')
class TestPflist:
    params = [
        ("fieldname", "fieldtype"),
        ("test1", "2"),
    ]

    @pytest.mark.parametrize("nam, typ,", params)
    def test_add_prompt_field_list(self, nam, typ, app):
        with app.app_context():
            crud.add_prompt_field_list(nam, typ)
            res = crud.get_prompt_field_list_all()
            assert {"name": nam, "type": typ} in res

    @pytest.mark.parametrize("nam, typ", params)
    def test_del_prompt_field_list(self, nam, typ, app):
        with app.app_context():
            crud.del_prompt_field_list(nam)
            res = crud.get_prompt_field_list_all()
            assert {"name": nam, "type": typ} not in res
