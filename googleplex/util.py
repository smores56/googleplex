import codecs
from functools import wraps
from os import environ
from os.path import join, dirname
import re
from threading import Thread
from time import sleep

from dotenv import load_dotenv
from jinja2 import Environment, PackageLoader, select_autoescape
import pyscrypt
from sanic import response
from sanic.exceptions import Forbidden

from . import models

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


def load_config():
    if load_config.CONFIG is None:
        fields = []
        load_config.CONFIG = {}
        for field in ['DB_USER', 'DB_NAME', 'DB_PASS', 'DB_HOST', 'SESSION_COOKIE_SECRET_KEY']:
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
            loader=PackageLoader('googleplex', 'templates'),
            autoescape=select_autoescape(['html'])
        )
        render_template.env.filters['datetime_fmt'] = datetime_fmt

    return response.html(render_template.env.get_template(name).render(**kwargs))


render_template.env = None


def authorized(premium=False, admin=False):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            user = models.User.load_if_logged_in(request)  # load user if they are logged in

            # the user exists and is authorized
            if user and (not premium or user.premium) and (not admin or user.admin):
                resp = await f(request, user, *args, **kwargs)
                return resp

            else:
                raise Forbidden("You must be logged in to visit the requested page.")

        return decorated_function

    return decorator


def scrypt(str_in, hash_str):
    hash_bytes = pyscrypt.hash(password=str_in.encode(),
                               salt=hash_str.encode(),
                               N=1024,
                               r=1,
                               p=1,
                               dkLen=32)
    return codecs.encode(hash_bytes, 'hex')


async def load_file(filename):
    return await response.file(join(dirname(__file__), filename))


email_pattern = re.compile('^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')


def validate_email(email):
    return email_pattern.match(email)


def datetime_fmt(date, fmt_str='%B %-d, %Y'):
    return date.strftime(fmt_str)


def schedule_cleanings():
    def run_cleaning():
        while True:
            models.Session.remove_expired()
            models.File.remove_unaccounted()
            models.Message.remove_floating()
            sleep(600)
    Thread(target=run_cleaning, daemon=True).start()
