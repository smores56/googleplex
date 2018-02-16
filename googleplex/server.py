from datetime import timedelta, datetime
import os
from peewee import DoesNotExist
from sanic import Sanic
from sanic.response import *

from .models import *
from .util import *

CONFIG = load_config()
app = Sanic(__name__)


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
