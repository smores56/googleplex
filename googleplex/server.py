from datetime import timedelta, datetime, date
import os
from peewee import DoesNotExist
from sanic import Sanic
from sanic.response import redirect
from sanic.response import json as json_resp
from sanic.exceptions import Forbidden, NotFound, ServerError

from .models import *
from .util import *
import json
CONFIG = load_config()
app = Sanic(__name__)

data = autocomplete()


@app.route('/')
@app.route('/index')
async def index(request):
    user = User.load_if_logged_in(request)
    return render_template('index.html', user=user, autoResults=json.dumps(data))


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
        return redirect('/') if user else render_template('login.html', flash=flash, user=user, autoResults=json.dumps(data))

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
                                                          user=user, flash=flash, autoResults=json.dumps(data))

    else:
        user, error = User.register(request.form)
        if error:
            response = redirect('/registration')
            response.cookies['flash'] = error
            return response

        else:
            message = ActiveLink.setup_link(user, 'activate account')
            response = redirect('/login')
            response.cookies['flash'] = message
            return response


@app.route('/password_reset', methods=['GET', 'POST'])
async def password_reset(request):
    if request.method == 'GET':
        active_link_str = request.args.get('link', '')
        active_link = ActiveLink.get_or_none(link=active_link_str)

        if (active_link and active_link.expire_time < datetime.now()) or \
                (active_link_str and not active_link):
            response = redirect('/login')
            response.cookies['flash'] = 'The link you clicked expired. ' \
                                        'Please request another one.'
            return response

        else:
            return render_template('password_reset.html', flash=request.cookies.get('flash'),
                                   link=active_link, autoResults=json.dumps(data))

    else:
        active_link_str = request.form.get('link', '')
        active_link = ActiveLink.get_or_none(link=active_link_str)
        if active_link:
            if active_link.expire_time >= datetime.now():
                new_pass_hash = request.form.get('new_pass_hash')
                new_pass_rehash = scrypt(new_pass_hash, (active_link.user.email + 'xyz')[:8])
                User.update(pass_hash=new_pass_rehash).where(
                    User.id == active_link.user.id).execute()

                active_link.activate()
                response = redirect('/login')
                response.cookies['flash'] = 'Your password has been reset!'
                return response

            else:
                response = redirect('/login')
                response.cookies['flash'] = 'Your reset link expired. Please request another one.'
                return response

        else:
            email = request.form.get('email', '')
            user = User.get_or_none(email=email)

            if user:
                response = redirect('/login')
                response.cookies['flash'] = ActiveLink.setup_link(user, 'reset password')

            else:
                response = redirect('/password_reset')
                response.cookies['flash'] = 'The specified email could not be found.'

            return response


@app.route('/activate_account')
async def activate_account(request):
    link = ActiveLink.get_or_none(link=request.args.get('link', ''))
    if link:
        link.activate()
        response = redirect('/login')
        response.cookies['flash'] = 'Your account has been activated!'
        return response

    else:
        raise Forbidden('The activation link was not valid.')


@app.route('/profile')
@authorized()
async def profile(request, user):
    return render_template('profile.html', user=user, autoResults=json.dumps(data))


@app.route('/faq')
async def faq(request):
    user = User.load_if_logged_in(request)
    return render_template('faq.html', user=user)


@app.route('/submit', methods=['GET', 'POST'])
@authorized()
async def submit(request, user):
    if request.method == 'GET':
        return render_template('submit.html', user=user, autoResults=json.dumps(data))

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
        return render_template('manual_submit.html', user=user, autoResults=json.dumps(data))

    else:
        return json_resp({'list_id': BestsellerList.from_json(request.json, user).id})


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

        return render_template('preview.html', user=user, **vals, autoResults=json.dumps(data))


@app.route('/results')
async def results(request):
    user = User.load_if_logged_in(request)
    search = request.args.get('search', '')
    searchType = request.args.get('type', 'list')

    # Get results based on type of search
    if searchType == "list":
        results = BestsellerList.search(search)
    elif searchType == "author":
        results = Author.search(search)
    elif searchType == "book":
        results = Bestseller.search(search)

    return render_template('results.html', user=user, **results, autoResults=json.dumps(data))


@app.route('/book')
async def book(request):
    user = User.load_if_logged_in(request)
    title = request.args.get('title', '')
    book_id = int(request.args.get('id', -1))
    bestseller = Bestseller.get_book(title, book_id)
    if not bestseller:
        raise NotFound('The specified bestseller could not be found in our system.')

    else:
        return render_template('book.html', bestseller=bestseller, user=user, autoResults=json.dumps(data))


@app.route('/book_edit', methods=["GET", "POST"])
async def book_edit(request):
    user = User.load_if_logged_in(request)
    title = request.args.get('title', '')
    book_id = request.args.get('id', -1)
    bestseller = Bestseller.get_book(title, book_id)
    if not bestseller:
        raise NotFound("The specified bestseller could not be found in our system.")

    else:
        # if its a POST request, we are editing an entry in the DB
        if request.method == "POST":
            # Get the description, title, and author name from the form, need ternaries because
            # forms dont add <key, value> pairs for empty values
            description = request.form['description'][0] if "description" in request.form.keys(
            ) else bestseller.description
            title = request.form['title'][0] if "title" in request.form.keys() else bestseller.title
            author_name = request.form['author'][0] if 'author' in request.form.keys() else None

            # Try to format the date into our format, if it fails just use the date
            # we already have
            try:
                published_date = datetime.strptime(request.form['published'][0], '%Y-%m-%d')
            except:
                published_date = bestseller.authored_date

            # Find the author in the DB, if they don't exist then create a new author entry
            author = Author.get_author(author_name)
            if author is None and author_name is not None:
                author_data = {'name': author_name}
                author = models.Author.create(**author_data)

            # Update the bestseller entry
            Bestseller.update(title=title, description=description, author=author,
                              authored_date=published_date
                              ).where(Bestseller.id == book_id).execute()

            # Redirect the user back to the book's entry page
            return redirect("/book?title={}&id={}".format(title, book_id))
        else:
            return render_template('book_edit.html', bestseller=bestseller, user=user, autoResults=json.dumps(data))


@app.route('/author_edit', methods=["GET", "POST"])
async def author_edit(request):
    user = User.load_if_logged_in(request)
    name = request.args.get('name', '')
    author = Author.get_author(name)
    if not author:
        raise NotFound('The specified author could not be found in our system.')

    else:
        # if its a POST request, we are editing an entry in the DB
        if request.method == "POST":
            # Get the name of the author
            keys = request.form.keys()
            name = request.form['name'][0] if 'name' in keys else author.name

            # Try to translate the date into our format, if it fails fallback to the date in the DB
            try:
                birth_date = datetime.strptime(request.form['birth_date'][0], '%Y-%m-%d')
            except:
                birth_date = author.birth_date

            # Try to translate the date into our format, if it fails fallback to the date in the DB
            try:
                death_date = datetime.strptime(request.form['death_date'][0], '%Y-%m-%d')
            except:
                death_date = author.death_date

            # Get the ethnicity of the author
            ethnicity = request.form['ethnicity'][0] if 'ethnicity' in keys else author.ethnicity

            # Update the entry and redirect the user to the author's entry page
            Author.update(name=name, birth_date=birth_date, death_date=death_date,
                          ethnicity=ethnicity).where(Author.name == name).execute()

            return redirect("/author?name={}".format(name))
        else:
            return render_template('author_edit.html', author=author, user=user, autoResults=json.dumps(data))


@app.route('/list')
async def bestseller_list(request):
    user = User.load_if_logged_in(request)
    title = request.args.get('title', '')
    list_id = int(request.args.get('id', -1))
    bestseller_list = BestsellerList.get_list(title, list_id)
    if not bestseller_list:
        raise NotFound('The specified bestseller list could not be found in our system.')

    else:
        bs_file = File.get_or_none(bestseller_list=bestseller_list)
        return render_template('list.html', list=bestseller_list, user=user, file=bs_file, autoResults=json.dumps(data))


@app.route('/list_edit', methods=["GET", "POST"])
async def bestseller_list(request):
    user = User.load_if_logged_in(request)
    title = request.args.get('title', '')
    list_id = int(request.args.get('id', -1))
    bestseller_list = BestsellerList.get_list(title, list_id)
    if not bestseller_list:
        raise NotFound('The specified bestseller list could not be found in our system.')

    else:
        # if its a POST request, we are editing an entry in the DB
        if request.method == "POST":
            form = request.form
            # Get the list title and description
            newTitle = request.form['title'][0]
            description = request.form['description'][0] if 'description' in form.keys(
            ) else bestseller_list.name

            # Empty the bestseller list so we can add in the edited list
            BestsellerListOrdering.clear_list(bestseller_list)

            # Loop through all the book titles, if the book does not exist add an entry
            # Add an entry to link the book to the list
            for i in range(len(form) - 2):
                book_title = form['book' + str(i + 1)][0]
                bestseller = Bestseller.get_or_none(Bestseller.title == book_title)
                if not bestseller:
                    bestseller = Bestseller.create(title=book_title)

                BestsellerListOrdering.create(
                    index=i + 1, bestseller=bestseller, bestseller_list=bestseller_list)

            # Update the list and redirect the user back to the list's page
            BestsellerList.update(title=newTitle, description=description).\
                where(BestsellerList.id == list_id).execute()

            return redirect("/list?title={}&id={}".format(title, list_id))
        else:
            return render_template('list_edit.html', list=bestseller_list, user=user, autoResults=json.dumps(data))


@app.route('/author')
async def book(request):
    user = User.load_if_logged_in(request)
    name = request.args.get('name', '')
    author = Author.get_author(name)
    if not author:
        raise NotFound('The specified author could not be found in our system.')

    else:
        return render_template('author.html', author=author, user=user, autoResults=json.dumps(data))


@app.route('/logout')
async def logout(request):
    if 'login_cookie' in request.cookies:
        response = redirect('/')
        del request.cookies['login_cookie']
        del response.cookies['login_cookie']
        return response


@app.exception(NotFound)
async def page_not_found(request, exception):
    return render_template('page_not_found.html', error=str(exception), autoResults=json.dumps(data))


@app.exception(Forbidden)
async def access_forbidden(request, exception):
    return render_template('access_forbidden.html', error=str(exception), autoResults=json.dumps(data))


@app.exception(ServerError)
async def internal_error(request, exception):
    return render_template('internal_error.html', error=str(exception), autoResults=json.dumps(data))


@app.middleware('response')
async def remove_flash(request, response):
    if 'flash' not in response.cookies:
        del response.cookies['flash']


@app.middleware('response')
async def set_expire_time_on_login_cookie(request, response):
    login_cookie = request.cookies.get('login_cookie', None)
    if login_cookie:
        response.cookies['login_cookie'] = login_cookie
        response.cookies['login_cookie']['max-age'] = 3600


def run():
    schedule_cleanings()
    app.run(host='127.0.0.1', port='5678')
