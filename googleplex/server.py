from datetime import timedelta, datetime, date
import os
from peewee import DoesNotExist
from sanic import Sanic
from sanic.response import *
from sanic.exceptions import Forbidden, NotFound, ServerError

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
    login_cookie = request.cookies.get('login_cookie')
    if login_cookie:
        if Session.from_cookie(login_cookie):
            return redirect('/')
        else:
            del request.cookies['login_cookie']

    if request.method == 'GET':
        flash = request.cookies.pop('flash', None)
        user = User.load_if_logged_in(request)
        return redirect('/') if user else render_template('login.html', flash=flash, user=user)

    else:
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


@app.route('/uploaded/<requested>')
@authorized()
async def uploaded(request, user, requested):
    return await load_file(os.path.join('./uploaded/', requested))


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


@app.route('/password_reset', methods=['GET', 'POST'])
async def password_reset(request):
    email = str(request.form.get('email'))
    print(email)
    if validate_email(email): # email is of right form
        try:
            user = User.get(email=email) #Check for user
            if user: # redirect to login
                flash = "We've sent a password reset link to your email address."
                #TODO: email message sent somewhere here
                return render_template('login.html',flash=flash)
        except DoesNotExist:
            # Email not registered to a user, flash error message on reset page
            flash = 'The given email does not match any user in our records.'
            return render_template('password_reset.html',flash=flash)
    else:
        return render_template('password_reset.html')

@app.route('/profile')
@authorized()
async def profile(request, user):
    return render_template('profile.html', user=user)


@app.route('/submit', methods=['GET', 'POST'])
@authorized()
async def submit(request, user):
    if request.method == 'GET':
        return render_template('submit.html', user=user)

    else:
        list_type = request.args.get('type', 'manual')
        vals = {'type': list_type}

        if list_type == 'file':
            bs_list = BestsellerList.from_form(request.form, user)
            bs_file = File.upload(request.files.get('file'), bs_list)
            vals['file_id'] = bs_file.id
        elif list_type == 'image':
            bs_list = BestsellerList.from_form(request.form, user)
            bs_image = File.upload(request.files.get('image'), bs_list)
            vals['image_id'] = bs_image.id

        vals['list_id'] = bs_list.id

        return redirect(app.url_for('preview', **vals))


@app.route('/manual_submit', methods=['GET', 'POST'])
@authorized()
async def manual_submit(request, user):
    if request.method == 'GET':
        return render_template('manual_submit.html', user=user)

    else:
        return json({'list_id': BestsellerList.from_json(request.json, user).id})


@app.route('/preview', methods=['GET', 'POST'])
@authorized()
async def preview(request, user):
    list_type = request.args.get('type', 'manual')
    vals = {'type': list_type}

    if request.method == 'POST':
        list_id = int(request.form.get('list_id', -1))
        bs_list = BestsellerList.get_by_id(list_id)
        tags = [Tag.get_or_create(name=tag.strip())[0]
                for tag in request.form.get('tags').split(',')]
        for tag in tags:
            TagBestsellerListJunction.create(bestseller_list=bs_list, tag=tag)

        if request.form.get('confirm', '') == 'yes':
            bs_list.active = True
            bs_list.save()
            bs_file = File.get_or_none(File.bestseller_list == bs_list)
            if bs_file:
                bs_file.expire_time = None
                bs_file.save()

        else:
            for bestseller in Bestseller.select().where(Bestseller.bestseller_list == bs_list):
                bestseller.delete_instance()
            bs_list.delete_instance()

        return redirect('/')

    else:
        vals['list'] = BestsellerList.get_by_id(request.args.get('list_id'))

        if list_type == 'manual':
            vals['orderings'] = BestsellerListOrdering.select().where(
                BestsellerListOrdering.bestseller_list == vals['list']).order_by(
                BestsellerListOrdering.index)
        elif list_type == 'file':
            bs_file = File.get_by_id(request.args.get('file_id'))
            vals['file_path'] = bs_file.path.split('/', 2)[2]
            vals['file_name'] = bs_file.name
        else:
            bs_image = File.get_by_id(request.args.get('image_id'))
            vals['image_path'] = bs_image.path.split('/', 2)[2]
            vals['image_name'] = bs_image.name

        return render_template('preview.html', user=user, **vals)


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
        print("here 1")
        results = Bestseller.search(search)

    return render_template('results.html', user=user, **results)


@app.route('/book')
async def book(request):
    user = User.load_if_logged_in(request)
    title = request.args.get('title', '')
    book_id = int(request.args.get('id', -1))
    bestseller = Bestseller.get_book(title, book_id)
    if not bestseller:
        raise NotFound('The specified bestseller could not be found in our system.')

    else:
        return render_template('book.html', bestseller=bestseller, user=user)

@app.route('/book_edit', methods=["GET", "POST"])
async def book_edit(request):
    user = User.load_if_logged_in(request)
    title = request.args.get('title', '')
    book_id = request.args.get('id', -1)
    bestseller = Bestseller.get_book(title, book_id)
    if not bestseller:
        raise NotFound("The specified bestseller could not be found in our system.")

    else:
        if request.method == "POST":
            description = request.form['description'][0] if "description" in request.form.keys() else bestseller.description
            title = request.form['title'][0] if "title" in request.form.keys() else bestseller.title
            author_name = request.form['author'][0] if 'author' in request.form.keys() else None
            try:
                published_date = datetime.strptime(request.form['published'][0], '%Y-%m-%d')
            except:
                published_date = bestseller.authored_date

            author = Author.get_author(author_name)
            if author is None and author_name is not None:
                author_data = {'name': author_name}
                author = models.Author.create(**author_data)

            Bestseller.update(title=title, description=description, author=author, authored_date=published_date).where(Bestseller.id == book_id).execute()

            return redirect("/book?title={}&id={}".format(title, book_id))
        else:
            return render_template('book_edit.html', bestseller=bestseller, user=user)

@app.route('/author_edit', methods=["GET", "POST"])
async def author_edit(request):
    user = User.load_if_logged_in(request)
    name = request.args.get('name', '')
    author = Author.get_author(name)
    if not author:
        raise NotFound('The specified author could not be found in our system.')

    else:
        if request.method == "POST":
            print(request.form)
            keys = request.form.keys()
            name = request.form['name'][0] if 'name' in keys else author.name
            try:
                birth_date = datetime.strptime(request.form['birth_date'][0], '%Y-%m-%d')
            except:
                birth_date = author.birth_date

            try:
                death_date = datetime.strptime(request.form['death_date'][0], '%Y-%m-%d')
            except:
                death_date = author.death_date
            ethnicity = request.form['ethnicity'][0] if 'ethnicity' in keys else author.ethnicity

            Author.update(name = name, birth_date=birth_date, death_date=death_date, ethnicity=ethnicity).where(Author.name == name).execute()

            return redirect("/author?name={}".format(name))
        else:
            return render_template('author_edit.html', author=author, user=user)


@app.route('/list')
async def bestseller_list(request):
    user = User.load_if_logged_in(request)
    title = request.args.get('title', '')
    list_id = int(request.args.get('id', -1))
    bestseller_list = BestsellerList.get_list(title, list_id)
    if not bestseller_list:
        raise NotFound('The specified bestseller list could not be found in our system.')

    else:
        return render_template('list.html', list=bestseller_list, user=user)


@app.route('/author')
async def book(request):
    user = User.load_if_logged_in(request)
    name = request.args.get('name', '')
    author = Author.get_author(name)
    if not author:
        raise NotFound('The specified author could not be found in our system.')

    else:
        return render_template('author.html', author=author, user=user)


@app.route('/logout')
async def logout(request):
    if 'login_cookie' in request.cookies:
        response = redirect('/')
        del request.cookies['login_cookie']
        del response.cookies['login_cookie']
        return response


@app.exception(NotFound)
async def page_not_found(request, exception):
    return render_template('page_not_found.html', error=str(exception))


@app.exception(Forbidden)
async def access_forbidden(request, exception):
    return render_template('access_forbidden.html', error=str(exception))


@app.exception(ServerError)
async def internal_error(request, exception):
    return render_template('internal_error.html', error=str(exception))


@app.middleware('response')
async def remove_flash(request, response):
    # TODO: if new flash is set, it will get deleted!
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
    schedule_cleanings()
