import itertools
import random
from threading import Thread
from time import sleep
from uuid import uuid4

from peewee import *
from datetime import timedelta, datetime
from playhouse.postgres_ext import *

from .util import *

CONFIG = load_config()

database = PostgresqlDatabase(
    CONFIG['DB_NAME'], **{
        'user': CONFIG['DB_USER'],
        'host': CONFIG['DB_HOST'],
        'password': CONFIG['DB_PASS']
    })


class UnknownField(object):
    def __init__(self, *_, **__): pass


class BaseModel(Model):

    class Meta:
        database = database


class Author(BaseModel):
    birth_date = DateField(null=True)
    death_date = DateField(null=True)
    ethnicity = TextField(null=True)
    name = TextField()

    class Meta:
        db_table = 'authors'

    @classmethod
    def search(cls, search_str, max_results=10, page=1):
        start = (page - 1) * max_results
        end = start + max_results
        lists = list(Author.select().where(Author.name.contains(search_str)))

        return {
            'results': list(itertools.islice(lists, start, end)),
            'num_results': len(lists),
            'start': start,
            'end': end
        }

    @classmethod
    def search_author(cls, author_name):
        return list(Author.select().where(Author.name == author_name))[0]

    def getInfo(self):
        info = {'author_name': self.name}
        if self.birth_date:
            info['birth_date'] = self.birth_date

        if self.death_date:
            info['death_date'] = self.death_date

        if self.ethnicity:
            info['ethnicity'] = self.ethnicity

        return info

class User(BaseModel):
    admin = BooleanField()
    email = TextField(unique=True)
    first_name = TextField()
    institution = TextField(null=True)
    is_banned = BooleanField()
    last_name = TextField()
    pass_hash = TextField()
    position = TextField(null=True)
    premium = BooleanField()

    @classmethod
    def load_if_logged_in(cls, request):
        login_cookie = request.cookies.get('login_cookie')
        if login_cookie:
            session = Session.from_cookie(login_cookie)
            if session:
                session.refresh()
                return session.user

        return None

    @classmethod
    def register(cls, form, premium=False, admin=False):
        vals = {}
        for field, field_name in [('email', 'Email'), ('first_name', 'First name'),
                                  ('last_name', 'Last name'), ('pass_hash', 'Password')]:
            val = form.get(field, None)
            if val is None:
                return (None, field_name + ' not specified.')
            else:
                vals[field] = val

        for opt_field in ['institution', 'position']:
            vals[opt_field] = form.get(opt_field, None)

        vals.update({'premium': premium, 'admin': admin})
        re_hash = scrypt(vals['pass_hash'], (vals['email'] + 'xyz')[:8])
        vals['pass_hash'] = re_hash

        try:
            user = User.create(**vals)
            return (user, None)

        except DoesNotExist as e:
            return (None, 'An unknown error occurred: %s' % e)

    class Meta:
        db_table = 'users'


class BestsellerList(BaseModel):
    author = ForeignKeyField(db_column='author_id', null=True, model=Author, to_field='id')
    authored_date = DateField(null=True)
    contributor = ForeignKeyField(db_column='contributor_id',
                                  null=True, model=User, to_field='id')
    description = TextField(null=True)
    num_bestsellers = IntegerField()
    submission_date = DateField()
    title = TextField()

    class Meta:
        db_table = 'bestseller_lists'

    @classmethod
    def search(cls, search_str, max_results=10, page=1):
        start = (page - 1) * max_results
        end = start + max_results
        lists = list(BestsellerList.select().where(BestsellerList.title.contains(search_str)))

        return {
            'results': list(itertools.islice(lists, start, end)),
            'num_results': len(lists),
            'start': start,
            'end': end
        }

    @classmethod
    def from_form(cls, form):
        pass


class Bestseller(BaseModel):
    author = TextField(null=True)
    bestseller_list = ForeignKeyField(db_column='bestseller_list_id',
                                      model=BestsellerList, to_field='id')
    description = TextField(null=True)
    links = HStoreField(null=True)
    title = TextField()

    class Meta:
        db_table = 'bestsellers'

    @classmethod
    def search(cls, search_str, max_results=10, page=1):
        start = (page - 1) * max_results
        end = start + max_results
        lists = list(Bestseller.select().where(Bestseller.title.contains(search_str)))

        return {
            'results': list(itertools.islice(lists, start, end)),
            'num_results': len(lists),
            'start': start,
            'end': end
        }

    @classmethod
    def searchAuthor(cls, author_name):
        lists = list(Bestseller.selct().where(Bestseller.author == author_name))

        return {
            'books': lists
        }


class File(BaseModel):
    bestseller_list = ForeignKeyField(db_column='bestseller_list_id',
                                      model=BestsellerList, to_field='id')
    name = TextField()
    path = TextField()

    class Meta:
        db_table = 'files'


class Message(BaseModel):
    recipient = ForeignKeyField(db_column='recipient_id', null=True, model=User, to_field='id')
    send_time = TextField()
    sender = ForeignKeyField(db_column='sender_id', null=True, model=User,
                             related_name='users_sender_set', to_field='id')
    subject = TextField()
    text = TextField()

    class Meta:
        db_table = 'messages'


class Review(BaseModel):
    authored_time = DateTimeField()
    bestseller_list = ForeignKeyField(db_column='bestseller_list_id',
                                      model=BestsellerList, to_field='id')
    rating = IntegerField()
    text = TextField()
    user = ForeignKeyField(db_column='user_id', null=True, model=User, to_field='id')

    class Meta:
        db_table = 'reviews'


class Search(BaseModel):
    saved_on = DateTimeField()
    search_str = TextField()
    user = ForeignKeyField(db_column='user_id', null=True, model=User, to_field='id')

    class Meta:
        db_table = 'searches'


class Session(BaseModel):
    expire_time = DateTimeField()
    uuid = TextField()
    user = ForeignKeyField(db_column='user_id', model=User, to_field='id')

    class Meta:
        db_table = 'sessions'

    @classmethod
    def for_user(cls, user_id, long_term=False):
        expire_t = datetime.now() + timedelta(hours=(72 if long_term else 1))
        return cls.create(expire_time=expire_t, uuid=str(uuid4()), user_id=user_id)

    def __str__(self):
        return '%s %s' % (self.user.id, self.uuid)

    @classmethod
    def setup_culler(cls):
        def culler():
            while True:
                cls.remove_expired()
                sleep(300)

        Thread(target=culler).start()

    @classmethod
    def remove_expired(cls):
        Session.delete().where(cls.expire_time < datetime.now()).execute()

    def refresh(self):
        now = datetime.now()
        an_hour_from_now = now + timedelta(hours=1)
        if self.expire_time < an_hour_from_now:
            self.update(expire_time=an_hour_from_now).execute()

    def from_cookie(cookie):
        if isinstance(cookie, str):
            user_id, uuid = cookie.split(' ')[:2]
            try:
                session = Session.get(user=user_id, uuid=uuid)
                if session:
                    if session.expire_time < datetime.now():
                        session.delete_instance()

                    else:
                        session.refresh()
                        return session

            except DoesNotExist:
                pass

        return None


class Tag(BaseModel):
    name = TextField()

    class Meta:
        db_table = 'tags'


class TagBestsellerListJunction(BaseModel):
    bestseller_list = ForeignKeyField(db_column='bestseller_list_id',
                                      model=BestsellerList, to_field='id')
    tag = ForeignKeyField(db_column='tag_id', model=Tag, to_field='id')

    class Meta:
        db_table = 'tag_bestseller_list_junction'
        indexes = (
            (('tag', 'bestseller_list'), True),
        )
        primary_key = CompositeKey('bestseller_list', 'tag')
