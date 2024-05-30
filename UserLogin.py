class UserLogin():
    def fromDB(self, user_id, db, Users):
        self.__user = db.session.query(Users.id).filter(Users.id == user_id)
       # self.__user_id = Users.query.filter(Users.id == user_id).all()[0].id
        return self

    def create(self, user):
        self.__user = user
        return self

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymus(self):
        return False

    def get_id(self):
        return str(self.__user)