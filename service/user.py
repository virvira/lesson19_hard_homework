from dao.user import UserDAO
import hashlib
from constants import PWD_HASH_SALT, PWD_HASH_ITERATIONS
import calendar
import datetime
import jwt


class UserService:
    def __init__(self, dao: UserDAO):
        self.dao = dao

    def get_one(self, uid):
        return self.dao.get_one(uid)

    def get_all(self):
        users = self.dao.get_all()
        return users

    def create(self, data):
        data["password"] = self.get_hash(data["password"])
        return self.dao.create(data)

    def update(self, data):
        self.dao.update(data)
        return self.dao

    def delete(self, uid):
        self.dao.delete(uid)

    def get_hash(self, password):
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),  # Convert the password to bytes
            PWD_HASH_SALT,
            PWD_HASH_ITERATIONS
        ).decode("utf-8", "ignore")

    def get_tokens(self, user_obj):
        min30 = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        user_obj["exp"] = calendar.timegm(min30.timetuple())
        access_token = jwt.encode(user_obj, PWD_HASH_SALT)

        day30 = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        user_obj["exp"] = calendar.timegm(day30.timetuple())
        refresh_token = jwt.encode(user_obj, PWD_HASH_SALT)
        return {"access_token": access_token, "refresh_token": refresh_token, "exp": user_obj["exp"]}

    def auth_user(self, username, password):
        user = self.dao.get_by_username(username)
        if not user:
            return None

        password_hash = self.get_hash(password)

        if password_hash != user.password:
            return None

        user_data = {
            "username": user.username,
            "role": user.role
        }
        tokens = self.get_tokens(user_data)

        return tokens

    def check_refresh_token(self, refresh_token):
        try:
            user_data = jwt.decode(jwt=refresh_token, key=PWD_HASH_SALT, algorithms=['HS256'])
        except Exception as e:
            return None

        return self.get_tokens(user_data)