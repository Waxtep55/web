from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_ngrok import run_with_ngrok
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import re, random

from UserLogin import UserLogin
# from random_quote import Generate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quotes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'a12eidksaa3rpfs4fkasdf'
db = SQLAlchemy(app)

run_with_ngrok(app)

#migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = '/login'
login_manager.login_message = 'Авторизуйтесь для доступа к этой странице'

class Quotes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(300), nullable=False)
    author = db.Column(db.String(60), nullable=False)
    composition = db.Column(db.String(100))
    character = db.Column(db.String(60))

    def __repr__(self):
        return '<Article %r>' % self.id

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(30), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    favourite = db.Column(db.String(100000))
    admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Article %r>' % self.id

def random_quote():
    id = random.randint(0, int(Quotes.query.count()))
    return Quotes.query.filter(Quotes.id == id).first()

@login_manager.user_loader
def load_user(user_id):
    return UserLogin().fromDB(user_id, db, Users)

@app.route('/test', methods=['POST', 'GET'])
def test():
    print(random_quote())
    if request.method == 'POST':
        print(request.form['кнопу'])
    return render_template('test.html')

@app.route('/create_quote', methods=['POST', 'GET'])
@login_required
def create_quote():
    if request.method == 'POST':
        text = request.form['text']
        author = request.form['author']
        composition = request.form['composition']
        character = request.form['character']

        if composition == '':
            composition = None
        if character == '':
            character = None

        quote = Quotes(text=text, author=author, composition=composition, character=character)

        try:
            db.session.add(quote)
            db.session.commit()
            return redirect('/create_quote')
        except:
            return "ОШИБКА ДОБАВЛЕНИЯ ЦИТАТЫ!"
    else:
        return render_template('create_quote.html')


@app.route('/', methods=['POST', "GET"])
@app.route('/home', methods=['POST', "GET"])
def main():
    if request.method == 'POST':
        quotes = Quotes.query.filter(Quotes.author.like(f'%{request.form["author"]}%'),
                                     Quotes.composition.like(f'%{request.form["composition"]}%'),
                                     Quotes.character.like(f'%{request.form["character"]}%'),
                                     Quotes.text.like(f'%{request.form["txt"]}%'))
        if current_user.is_authenticated:
            if current_user.admin:
                return render_template('main_admin.html', quotes=quotes, rand_quote=random_quote())
            return render_template('main_login.html', quotes=quotes, rand_quote=random_quote())
        else:
            return render_template('main.html', quotes=quotes, rand_quote=random_quote())

    quotes = Quotes.query.order_by(Quotes.id.desc()).all()
    if current_user.is_authenticated:
        if current_user.admin:
            return render_template('main_admin.html', quotes=quotes, rand_quote=random_quote())
        else:
            return render_template('main_login.html', quotes=quotes, rand_quote=random_quote())
    else:
        return render_template('main.html', quotes=quotes, rand_quote = random_quote())


@app.route('/add_to_favourite', methods=['POST'])
@login_required  # Убедитесь, что пользователь аутентифицирован
def add_to_favourite():
    quote_id = request.form.get('quote_id')

    if not quote_id:
        flash('Цитата не найдена.', 'error')
        return redirect(url_for('main_admin'))

    # Получаем текущего пользователя
    id = current_user.get_id()
    user = Users.query.filter(Users.id == id).first()
    # Проверяем, есть ли уже избранные цитаты
    if user.favourite:
        favourites = user.favourite.split()
        if quote_id not in favourites:
            favourites.append(quote_id)
            user.favourite = ' '.join(favourites)
    else:
        user.favourite = quote_id

    # Сохраняем изменения в базе данных
    db.session.commit()

    return redirect(url_for('main_admin'))

@app.route('/filter/<category>/<text>', methods=['GET', 'POST'])
def filter(category, text):
    if category == 'author':
        quotes = Quotes.query.filter(Quotes.author == text).all()
    elif category == 'composition':
        quotes = Quotes.query.filter(Quotes.composition == text).all()
    else:
        quotes = Quotes.query.filter(Quotes.character == text).all()
    if current_user.is_authenticated:
        if current_user.admin:
            return render_template('filter_admin.html', quotes=quotes, rand_quote=random_quote())
        else:
            return render_template('filter_login.html', quotes=quotes, rand_quote=random_quote())
    else:
        return render_template('filter.html', quotes=quotes, rand_quote=random_quote())


@app.route('/favourite', methods=['GET'])
@login_required  # Убедитесь, что пользователь аутентифицирован
def favourite_quotes():
    id = current_user.get_id()
    user = Users.query.filter(Users.id == id).first()
    if user.favourite:
        # Разделяем строку с ID цитат и преобразуем в список целых чисел
        quote_ids = list(map(int, user.favourite.split()))
        # Получаем все избранные цитаты по их ID
        quotes = Quotes.query.filter(Quotes.id.in_(quote_ids)).all()
    else:
        quotes = []  # Если нет избранных цитат, возвращаем пустой список
    if current_user.admin:
        return render_template('favourite_quotes_admin.html', quotes=quotes)
    return render_template('favourite_quotes.html', quotes=quotes)


@app.route('/remove_from_favourite', methods=['POST'])
@login_required  # Убедитесь, что пользователь аутентифицирован
def remove_from_favourite():
    id = current_user.get_id()
    user = Users.query.filter(Users.id == id).first()
    quote_id = request.form.get('quote_id')

    if not quote_id:
        return redirect(url_for('favourite_quotes', message='Цитата не найдена.'))

    if user.favourite:
        favourites = user.favourite.split()

        if quote_id in favourites:
            favourites.remove(quote_id)
            user.favourite = ' '.join(favourites)
            db.session.commit()
            return redirect(url_for('favourite_quotes'))
        else:
            return redirect(url_for('favourite_quotes'))
    else:
        return redirect(url_for('favourite_quotes'))


@app.route('/login', methods=['POST', "GET"])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        if db.session.query(Users).filter(Users.login == login).count() != 0:
            user = db.session.query(Users).filter(Users.login == login).first()
            if check_password_hash(user.password, password):
                userlogin = UserLogin().create(user)
                login_user(userlogin)
                if user.admin:  # Если пользователь - админ
                    return redirect('/main_admin')  # Перенаправление на админ-панель
                else:
                    return redirect(request.args.get('next') or '/home')
        flash('Неверный логин или пароль')
        return redirect('/login')
    else:
        if current_user.is_authenticated:
            return redirect('/')
        return render_template('login.html')

@app.route('/reg',  methods=['POST', 'GET'])
def reg():
    pattern_login = r'^(?=[a-zA-Z][a-zA-Z0-9]*$).{4,}$'
    pattern_password = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    pattern_email = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if request.method == 'POST':
        login = request.form['login']
        email = request.form['email']
        password = request.form['password']
        if db.session.query(Users).filter(Users.login == login).count() != 0:
            flash('Пользователь с таким логином уже существует')
        elif db.session.query(Users).filter(Users.email == email).count() != 0:
            flash('Пользователь с такой почтой уже зарегистрирован')
        elif not re.match(pattern_login, login):
            flash('Логин должен содержать минимум 4 символа, содержать только латинские символы и не может начинаться с цифры или спецсимвола')
        elif not re.match(pattern_email, email):
            flash('Почта должна иметь вид: example@somemail.com')
        elif not re.match(pattern_password, password):
            flash('Пароль должен содержать минимум 8 символов, только латинские символы, заглавные и строчные буквы и хотя бы одну цифру и один спецсимвол')
        else:
            flash('Регистрация прошла успешно!')
            user = Users(login=login, password=generate_password_hash(password), email=email)
            try:
                db.session.add(user)
                db.session.commit()
                return redirect('/login')
            except:
                return "ОШИБКА РЕГИСТРАЦИИ"
    if current_user.is_authenticated:
        return redirect('/')
    return render_template('register.html')

@app.route('/about')
def about():
    if current_user.is_authenticated:
        if current_user.admin:
            return render_template('about_admin.html')
        else:
            return render_template('about_login.html')
    else:
        return render_template('about.html')

@app.route('/categories')
def categories():
    quotes = Quotes.query.all()
    authors = []
    compositions = []
    characters = []
    for quote in quotes:
        authors.append(quote.author)
        compositions.append(quote.composition)
        characters.append(quote.character)
    authors = list(set(authors))
    compositions = list(set(compositions))
    characters = list(set(characters))
    if current_user.is_authenticated:
        if current_user.admin:
            return render_template('categories_admin.html', authors=authors, compositions=compositions, characters=characters)
        else:
            return render_template('categories_login.html', authors=authors, compositions=compositions, characters=characters)
    else:
        return render_template('categories.html', authors=authors, compositions=compositions, characters=characters)

@app.route('/search')
def search():
    return render_template('search.html')

@app.route('/main_admin', methods=['GET', 'POST'])
@login_required  # Защита маршрута, чтобы только авторизованные пользователи могли получить доступ
def main_admin():
    if request.method == 'POST':
        quotes = Quotes.query.filter(Quotes.author.like(f'%{request.form["author"]}%'),
                                     Quotes.composition.like(f'%{request.form["composition"]}%'),
                                     Quotes.character.like(f'%{request.form["character"]}%'),
                                     Quotes.text.like(f'%{request.form["txt"]}%'))
        if current_user.is_authenticated:
            if current_user.admin:
                return render_template('main_admin.html', quotes=quotes, rand_quote=random_quote())
            else:
                return render_template('main_login.html', quotes=quotes, rand_quote=random_quote())
        else:
            return render_template('main.html', quotes=quotes, rand_quote=random_quote())

    quotes = Quotes.query.order_by(Quotes.id.desc()).all()
    if current_user.admin:  # Проверка, является ли текущий пользователь администратором
        return render_template('main_admin.html', quotes=quotes, rand_quote=random_quote())  # Отображение шаблона админ-панели
    else:
        return redirect('/home')  # Если не админ, перенаправляем на главную страницу


@app.route('/user_moderation', methods=['GET', 'POST'])
@login_required
def user_moderation():
    if current_user.is_authenticated:
        if not current_user.admin:
            return redirect('/home')

        if request.method == 'POST':
            login_filter = f'%{request.form["login"]}%' if request.form["login"] else '%'
            email_filter = f'%{request.form["email"]}%' if request.form["email"] else '%'
            admin_filter = request.form.get("admin", None)

            users_query = Users.query.filter(
                Users.login.like(login_filter),
                Users.email.like(email_filter)
            )

            if admin_filter == '1':
                users_query = users_query.filter(Users.admin.is_(True))
            elif admin_filter == '0':
                users_query = users_query.filter(Users.admin.is_(False))

            users = users_query.all()
            return render_template('user_moderation.html', users=users)

        else:
            users = Users.query.order_by(Users.id.desc()).all()

        return render_template('user_moderation.html', users=users)

    return redirect('/home')


@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.admin:
        return redirect('/home')

    user = Users.query.get_or_404(user_id)

    if request.method == 'POST':
        login = request.form['login']
        email = request.form['email']
        password = request.form['password']
        is_admin = 'admin' in request.form  # Проверяем, установлен ли чекбокс

        # Обновляем данные пользователя
        user.login = login
        user.email = email

        # Если пароль не пустой, хешируем его и обновляем
        if password:
            user.password = generate_password_hash(password)

        user.admin = is_admin

        db.session.commit()
        return redirect('/user_moderation')

    return render_template('edit_user.html', user=user)

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.is_authenticated and current_user.admin:
        user_to_delete = Users.query.get(user_id)
        if user_to_delete:
            db.session.delete(user_to_delete)
            db.session.commit()
    return redirect('/user_moderation')

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')

@app.route('/delete_quote/<int:quote_id>', methods=['POST'])
@login_required
def delete_quote(quote_id):
    quote = Quotes.query.get(quote_id)
    if quote:
        db.session.delete(quote)
        db.session.commit()
    return redirect('/main_admin')  # Перенаправление обратно на главную страницу админа

@app.route('/edit_quote/<int:quote_id>', methods=['GET', 'POST'])
@login_required
def edit_quote(quote_id):
    quote = Quotes.query.get_or_404(quote_id)  # Получаем цитату по ID или 404, если не найдена

    if request.method == 'POST':
        quote.text = request.form['text']
        quote.author = request.form['author']
        quote.composition = request.form['composition'] or None
        quote.character = request.form['character'] or None

        try:
            db.session.commit()  # Сохраняем изменения
            return redirect('/main_admin')  # Перенаправляем обратно на страницу админа
        except:
            return "ОШИБКА ОБНОВЛЕНИЯ ЦИТАТЫ!"

    return render_template('edit_quote.html', quote=quote)  # Отображаем форму редактирования

# используется для генерации случайных цитат
"""@app.route('/generate')
def generate():
    generate_quote = Generate()
    generate_quote.generate(db, Quotes)
    return render_template('generate.html')"""

if __name__ == '__main__':
    app.run()