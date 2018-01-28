from os import environ
from os.path import join, dirname
from dotenv import load_dotenv
from functools import wraps
from sanic.response import html
from jinja2 import Environment, PackageLoader, select_autoescape
import pyscrypt

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


def load_config():
    if load_config.CONFIG is None:
        fields = []
        load_config.CONFIG = {}
        for field in ['DATABASE_URL', 'DB_USER', 'DB_NAME', 'DB_PASS', 'DB_HOST',
                      'SESSION_COOKIE_SECRET_KEY']:
            value = environ.get(field, None)
            if value is None:
                raise KeyError('The environment variable "%s" was not set. Please set it in \
                the related .env file.' % field)

            else:
                load_config.CONFIG[field] = value

    return load_config.CONFIG


load_config.CONFIG = None


def render_template(name, **kwargs):
    if render_template.env is None:
        render_template.env = Environment(
            loader=PackageLoader('__main__', 'templates'),
            autoescape=select_autoescape(['html'])
        )

    return html(render_template.env.get_template(name).render(**kwargs))


render_template.env = None


def authorized(premium=False, admin=False):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            user = User.load_if_logged_in(request)  # load user if they are logged in

            # the user exists and is authorized
            if user and (not premium or user.premium) and (not admin or user.admin):
                response = await f(request, user, *args, **kwargs)
                return response

            else:
                return json({'status': 'not_authorized'}, 403)

        return decorated_function

    return decorator


def scrypt(str_in, hash_str):
    return pyscrypt.hash(password=str_in,
                         salt=hash_str,
                         N=1024,
                         r=1,
                         p=1,
                         dkLen=32).encode('hex')
