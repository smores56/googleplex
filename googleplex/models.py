from datetime import timedelta, datetime, date, time
import itertools
import random
from threading import Thread
from time import sleep
from uuid import uuid4

from peewee import *

from .util import *

CONFIG = load_config()

database = PostgresqlDatabase(
    CONFIG['DB_NAME'], **{
        'user': CONFIG['DB_USER'],
        'host': CONFIG['DB_HOST'],
        'password': CONFIG['DB_PASS']
    })


class BaseModel(Model):

    class Meta:
        database = database


class Author(BaseModel):
    birth_date = DateField(null=True)
    death_date = DateField(null=True)
    ethnicity = TextField(null=True)
    name = TextField()

    @property
    def books(self):
        return list(Bestseller.select().where(Bestseller.author == self))

    @property
    def age(self):
        if not hasattr(self, '_age'):
            if self.birth_date:
                end_date = self.death_date or date.today()
                end_bday = date(end_date.year, self.birth_date.month, self.birth_date.day)

                self._age = end_date.year - self.birth_date.year
                if end_bday > end_date:
                    self._age -= 1

            else:
                self._age = None

        return self._age

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
    def get_author(cls, author_name):
        return Author.get_or_none(Author.name == author_name)


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

    @property
    def full_name(self):
        return "%s %s" % (self.first_name, self.last_name)

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


class BestsellerList(BaseModel):
    author = ForeignKeyField(null=True, model=Author)
    authored_date = DateField(null=True)
    contributor = ForeignKeyField(null=True, model=User)
    description = TextField(null=True)
    num_bestsellers = IntegerField()
    submission_date = DateField()
    title = TextField()

    @property
    def bestsellers(self):
        return [ordering.bestseller for ordering in BestsellerListOrdering.select().where(
            BestsellerListOrdering.bestseller_list == self).order_by(BestsellerListOrdering.index)]

    @property
    def tags(self):
        return [j.tag for j in TagBestsellerListJunction.select()
                .where(TagBestsellerListJunction.bestseller_list == self)]

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
    def get_list(cls, list_title, list_id):
        return BestsellerList.get_or_none((BestsellerList.title == list_title) and
                                          (BestsellerList.id == list_id))

    @classmethod
    def from_form(cls, form):
        raise NotImplemented


class Bestseller(BaseModel):
    author = ForeignKeyField(model=Author, null=True)
    description = TextField(null=True)
    title = TextField()

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
    def get_book(cls, book_title, book_id):
        return Bestseller.get_or_none((Bestseller.title == book_title) and
                                      (Bestseller.id == book_id))

    def get_lists_with_this_bestseller(self):
        return [ordering.bestseller_list for ordering in
                BestsellerListOrdering.select().where(BestsellerListOrdering.bestseller == self)]


class BestsellerListOrdering(BaseModel):
    bestseller_list = ForeignKeyField(model=BestsellerList)
    bestseller = ForeignKeyField(model=Bestseller)
    index = IntegerField()


class File(BaseModel):
    bestseller_list = ForeignKeyField(model=BestsellerList)
    name = TextField()
    path = TextField()


class Message(BaseModel):
    recipient = ForeignKeyField(null=True, model=User)
    send_time = TextField()
    sender = ForeignKeyField(null=True, model=User)
    subject = TextField()
    text = TextField()


class Search(BaseModel):
    saved_on = DateTimeField()
    comment = TextField()
    search_str = TextField()
    user = ForeignKeyField(model=User)


class Session(BaseModel):
    expire_time = DateTimeField()
    uuid = TextField()
    user = ForeignKeyField(model=User)

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


class TagBestsellerListJunction(BaseModel):
    bestseller_list = ForeignKeyField(model=BestsellerList)
    tag = ForeignKeyField(model=Tag)

    class Meta:
        primary_key = CompositeKey('bestseller_list', 'tag')


MODELS = [Author, User, Bestseller, BestsellerList, BestsellerListOrdering,
          File, Message, Search, Session, Tag, TagBestsellerListJunction]

database.create_tables(MODELS, safe=True)
