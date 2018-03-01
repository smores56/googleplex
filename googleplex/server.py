from datetime import timedelta, datetime, date
import os
from peewee import DoesNotExist
from sanic import Sanic
from sanic.response import *

from .models import *
from .util import *

CONFIG = load_config()
app = Sanic(__name__)

DATE_FORMAT_STRING = '%B %-d, %Y'

@app.route('/')
@app.route('/index')
async def index(request):
    user = User.load_if_logged_in(request)
    return render_template('index.html', user=user)


@app.route('/login', methods=['POST', 'GET'])
async def login(request):
    if request.method == 'GET':
        flash = request.cookies.pop('flash', None)
        user = User.load_if_logged_in(request)
        return redirect('/') if user else render_template('login.html', flash=flash, user=user)

    else:
        login_cookie = request.cookies.get('login_cookie')
        if login_cookie:
            response = redirect('/')
            if Session.from_cookie(login_cookie):
                del response.cookies['login_cookie']
            return response

        email = request.form.get('email')
        pass_hash = request.form.get('pass_hash')
        remember_me = request.form.get('remember')

        if validate_email(email) and len(pass_hash) == 32:
            re_hash = scrypt(pass_hash, (email + 'xyz')[:8])
            try:
                user = User.get(email=email, pass_hash=re_hash)
                session = Session.for_user(user.id, long_term=remember_me)
                response = redirect('/')
                response.cookies['login_cookie'] = str(session)
                response.cookies['login_cookie']['max-age'] = (
                    session.expire_time - datetime.now()).total_seconds()
                return response

            except DoesNotExist:
                pass

        response = redirect('/login')
        response.cookies['flash'] = 'The given email/password combination does \
                                     not match any user in our records.'

        return response


@app.route('/favicon.ico')
async def favicon(request):
    return await load_file('./static/images/favicon.ico')


@app.route('/images/<image>')
async def images(request, image):
    return await load_file(os.path.join('./static/images/', image))


@app.route('/scripts/<script>')
async def scripts(request, script):
    return await load_file(os.path.join('./static/scripts/', script))


@app.route('/styles/<sheet>')
async def styles(request, sheet):
    return await load_file(os.path.join('./static/styles/', sheet))


@app.route('/registration', methods=['GET', 'POST'])
async def registration(request):
    if request.method == 'GET':
        user = User.load_if_logged_in(request)
        flash = request.cookies.get('flash', None)
        return redirect('/') if user else render_template('registration.html',
                                                          user=user, flash=flash)

    else:
        user, error = User.register(request.form)
        if error:
            response = redirect('/registration')
            response.cookies['flash'] = error
            return response

        else:
            return redirect('/login')


@app.route('/profile')
@authorized()
async def profile(request, user):
    return render_template('profile.html', user=user)


@app.route('/submit')
@authorized()
async def submit(request, user):
    return render_template('submit.html', user=user)


@app.route('/manual_submit')
@authorized()
async def manual_submit(request, user):
    return render_template('manual_submit.html', user=user)


@app.route('/preview')
@authorized()
async def preview(request, user):
    return render_template('preview.html', user=user)


@app.route('/results')
async def results(request):
    user = User.load_if_logged_in(request)
    search = request.args.get('search', '')
    searchType = request.args.get('type', 'list')

    if searchType == "list":
        results = BestsellerList.search(search)
    elif searchType == "author":
        results = Author.search(search)
    elif searchType == "book":
        results = Bestseller.search(search)

    return render_template('results.html', user=user, **results)

@app.route('/manualpreview', methods=['GET','POST'])
async def manualPreview(request):
    data = request.json
    listTitle = data.get('list_title')
    bookCount = data.get('book_count')
    for i in range(1, 1 + bookCount):
        book = data.get('book' + str(i))
        author = book.get('author')
        year = book.get('yearPublished')
        title = book.get('bookTitle')
    return render_template('preview.html')

@app.route('/logout')
async def logout(request):
    if 'login_cookie' in request.cookies:
        response = redirect('/')
        del request.cookies['login_cookie']
        del response.cookies['login_cookie']
        return response

@app.route('/book')
async def book(request):
    title = request.args.get('title', '')
    book_id = int(request.args.get('id', ''))
    book = Bestseller.get_book(title, book_id)

    book_info = {k:v for k,v in book.getInfo().items() if v}
    if 'author' in book_info.keys():
        book_info['author_id'] = book_info['author'].id
        book_info['author'] = book_info['author'].name

    return render_template('book.html', **book_info)

@app.route('/list')
async def list(request):
    title = request.args.get('title', '')
    list_id = request.args.get('id', '')

    bestsellerList = BestsellerList.get_list(title, list_id)

    list_info = {k:v for k, v in bestsellerList.getInfo().items() if v}

    list_info['books'] = Bestseller.get_books_on_list(list_id)
    list_info['submission_date'] = list_info['submission_date'].strftime(DATE_FORMAT_STRING)
    list_info['contributor'] = list_info['contributor'].first_name + " " + list_info['contributor'].last_name

    if 'authored_date' in list_info.keys():
        list_info['authored_date'] = list_info['authored_date'].strftime(DATE_FORMAT_STRING)


    print(list_info)

    return render_template('list.html', **list_info)

@app.route('/author')
async def book(request):

    name = request.args.get('name', '')
    author_id = int(request.args.get('id', ''))
    author = Author.get_author(name, author_id)

    author_info = {k:v for k, v in author.getInfo().items() if v}

    if 'birth_date' in author_info.keys():
        birth_date = author_info['birth_date']
        arr = ['Birth Date: ' + birth_date.strftime(DATE_FORMAT_STRING)]
        if 'death_date' in author_info.keys():
            age_end = author_info['death_date']
            arr.append("Deceased: " + author_info['death_date'].strftime(DATE_FORMAT_STRING))
        else:
            age_end = datetime.date(datetime.now())

        calc_bday = date(age_end.year, birth_date.month, birth_date.day)
        age = age_end.year - birth_date.year
        if calc_bday > age_end:
            age -= 1

        arr.append("Age: " + str(age))

        author_info['age_string'] = ', '.join(arr)

    author_info['books'] = Bestseller.get_books_by_author(author)

    return render_template('author.html', **author_info)

@app.middleware('response')
async def remove_flash(request, response):
    if 'flash' in request.cookies:
        del response.cookies['flash']


@app.middleware('response')
async def set_expire_time_on_login_cookie(request, response):
    login_cookie = request.cookies.get('login_cookie', None)
    if login_cookie:
        response.cookies['login_cookie'] = login_cookie
        response.cookies['login_cookie']['max-age'] = 3600


def run():
    app.run(host='127.0.0.1', port='5678')
    Session.setup_culler()
