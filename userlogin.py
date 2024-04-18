from flask_login import UserMixin

from utils import utc


class UserLogin(UserMixin):
    def fromDB(self, id, db):
        self.__user = db.get_user(id)
        return self

    def create(self, user):
        self.__user = user
        return self

    def get_id(self) -> int:
        if self.__user:
            return self.__user.id  # was str(self.__user.id) ??

    def get_data(self):
        if self.__user:
            return self.__user.as_dict()

    def get_status(self):
        if self.__user:
            active = "active" if self.__user.active else "not active"
            email = self.__user.email
            tokens = self.__user.tokens
            reg_date = utc(self.__user.reg_date)
            exp_date = utc(self.__user.exp_date)
            return f"""Status: {active} | Email: {email} | registration date: {reg_date} | expire date: {exp_date} | tokens: {tokens}"""

        return "not available"

    # def is_authenticated(self):
    #     return True

    # def is_active(self):
    #     return True

    # def is_anonymous(self):
    #     return False
