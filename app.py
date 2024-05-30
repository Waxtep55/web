from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import distinct
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

    def __repr__(self):
        return '<Article %r>' % self.id

def random_quote():
    id = random.randint(0, int(Quotes.query.count()))
    return Quotes.query.filter(Quotes.id == id).first()

@login_manager.user_loader
def load_user(user_id):
    print('load_user')
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
            return render_template('main_login.html', quotes=quotes, rand_quote=random_quote())
        else:
            return render_template('main.html', quotes=quotes, rand_quote=random_quote())

    quotes = Quotes.query.order_by(Quotes.id.desc()).all()
    if current_user.is_authenticated:
        return render_template('main_login.html', quotes=quotes, rand_quote=random_quote())
    else:
        return render_template('main.html', quotes=quotes, rand_quote = random_quote())

@app.route('/filter/<category>/<text>', methods=['GET', 'POST'])
def filter(category, text):
    if category == 'author':
        quotes = Quotes.query.filter(Quotes.author == text).all()
    elif category == 'composition':
        quotes = Quotes.query.filter(Quotes.composition == text).all()
    else:
        quotes = Quotes.query.filter(Quotes.character == text).all()
    if current_user.is_authenticated:
        return render_template('filter_login.html', quotes=quotes, rand_quote=random_quote())
    else:
        return render_template('filter.html', quotes=quotes, rand_quote=random_quote())


@app.route('/favourite')
@login_required
def favourite():
    fav_quotes = Users.query.filter(Users.id == current_user.get_id()).first().favourite.split(' ')
    quotes = Quotes.query.filter(Quotes.id.in_(fav_quotes)).order_by(Quotes.id.desc()).all()
    return render_template('favourite.html', quotes=quotes)

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
        return render_template('categories_login.html', authors=authors, compositions=compositions, characters=characters)
    else:
        return render_template('categories.html', authors=authors, compositions=compositions, characters=characters)

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')

# используется для генерации случайных цитат
"""@app.route('/generate')
def generate():
    generate_quote = Generate()
    generate_quote.generate(db, Quotes)
    return render_template('generate.html')"""

if __name__ == '__main__':
    app.run(debug=True)