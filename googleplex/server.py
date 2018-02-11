import os
from .models import *
from .util import *

from peewee import DoesNotExist
from sanic import Sanic
from sanic.response import *
import sanic_cookiesession

CONFIG = load_config()
app = Sanic(__name__)

app.config['SESSION_COOKIE_SECRET_KEY'] = CONFIG['SESSION_COOKIE_SECRET_KEY']
sanic_cookiesession.setup(app)




@app.route('/')
@app.route('/index')
async def index(request):
    user = User.load_if_logged_in(request)
    return render_template('index.html', user=user)


@app.route('/login', methods=['POST', 'GET'])
async def login(request):
    if request.method == 'GET':
        session = request['session']
        flash = session.popitem()[1] if 'flash' in session else None
        user = User.load_if_logged_in(request)

        return redirect('/') if user else render_template('login.html', flash=flash)

    else:
        email = request.form.get('email')
        pass_hash = request.form.get('pass_hash')
        re_hash = scrypt(pass_hash, (email + 'xyz')[:8])
        try:
            user = User.get(email=email, pass_hash=re_hash)
            session = Session(user)
            request['session']['login_cookie'] = str(session)
            return redirect('/')

        except DoesNotExist:
            request['session']['flash'] = 'The given email/password combination does \
                                           not match any user in our records.'
            return redirect('/login')


@app.route('/favicon.ico')
async def favicon(request):
    return await load_file('/static/images/favicon.ico')


@app.route('/images/<image>')
async def images(request, image):
    return await load_file(os.path.join('./static/images/', image))


@app.route('/scripts/<script>')
async def scripts(request, script):
    return await load_file(os.path.join('./static/scripts/', script))


@app.route('/styles/<sheet>')
async def styles(request, sheet):
    return await load_file(os.path.join('./static/styles/', sheet))

@app.route('/registration')
async def registration(request):
    return render_template('registration.html')

@app.route('/profile')
@authorized()
async def profile(request, user):
    return render_template('profile.html')


@app.route('/submit')
@authorized()
async def submit(request, user):
    return render_template('submit.html')


@app.route('/manual_submit')
@authorized()
async def manual_submit(request, user):
    return render_template('manual_submit.html')


@app.route('/preview')
@authorized()
async def preview(request, user):
    return render_template('preview.html')


@app.route('/results')
async def results(request):
    search = request.args.get('search', '')
    results = BestsellerList.search(search)
    return render_template('results.html', **results)


def run():
    app.run(host='127.0.0.1', port='5678')
