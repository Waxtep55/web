class UserLogin():
    def __init__(self):
        self.__user = None
        self.admin = False  # Добавляем поле admin

    def fromDB(self, user_id, db, Users):
        self.__user = db.session.query(Users).filter(Users.id == user_id).first()
        if self.__user:
            self.admin = self.__user.admin  # Получаем значение admin из базы данных
        return self

    def create(self, user):
        self.__user = user
        self.admin = user.admin  # Сохраняем значение admin при создании
        return self

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):  # Исправлено на правильное название метода
        return False

    def get_id(self):
        return str(self.__user.id) if self.__user else None  # Возвращаем id пользователя