from datetime import timedelta, datetime, date, time
import itertools
import random
import os
from uuid import uuid4
from glob import glob
import imghdr

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
    def search(cls, search_str, max_results=25, page=1):
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
    admin = BooleanField(default=False)
    email = TextField(unique=True)
    first_name = TextField()
    institution = TextField(null=True)
    banned = BooleanField(default=False)
    last_name = TextField()
    pass_hash = TextField()
    position = TextField(null=True)
    premium = BooleanField(default=False)
    active = BooleanField(default=False)

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

            else:
                del request.cookies['login_cookie']

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

        vals.update({'premium': premium, 'admin': admin, 'banned': False})
        re_hash = scrypt(vals['pass_hash'], (vals['email'] + 'xyz')[:8])
        vals['pass_hash'] = re_hash

        try:
            user = User.create(**vals)
            return (user, None)

        except DoesNotExist as e:
            return (None, 'An unknown error occurred: %s' % e)


class BestsellerList(BaseModel):
    author = ForeignKeyField(null=True, model=Author, on_delete='SET NULL')
    authored_date = DateField(null=True)
    contributor = ForeignKeyField(null=True, model=User, on_delete='SET NULL')
    description = TextField(null=True)
    num_bestsellers = IntegerField()
    submission_date = DateField()
    title = TextField()
    active = BooleanField(default=False)

    @property
    def bestsellers(self):
        return [ordering.bestseller for ordering in BestsellerListOrdering.select().where(
            BestsellerListOrdering.bestseller_list == self).order_by(BestsellerListOrdering.index)]

    @property
    def tags(self):
        return [j.tag for j in TagBestsellerListJunction.select()
                .where(TagBestsellerListJunction.bestseller_list == self)]

    @classmethod
    def search(cls, search_str, max_results=25, page=1):
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
    def from_form(cls, form, user=None):
        vals = {'contributor': user, 'submission_date': date.today()}
        vals['title'] = form.get('title')
        vals['num_bestsellers'] = form.get('num_bestsellers')

        if 'description' in form:
            vals['description'] = form.get('description')
        if 'authored_date' in form:
            vals['authored_date'] = datetime.strptime(form['authored_date'][0], '%Y-%m-%d').date()
        if 'author' in form:
            vals['author'] = Author.get_or_create(name=form.get('author'))[0]

        return BestsellerList.create(**vals)

    @classmethod
    def from_json(cls, json, user):
        vals = {'contributor': user, 'submission_date': date.today(),
                'active': False, 'title': json.get('title'),
                'description': json.get('description') if 'description' in json else None}
        if 'author' in json:
            vals['author'] = Author.get_or_create(name=json.get('author'))[0]
        else:
            vals['author'] = None
        if 'authored_date' in json:
            vals['authored_date'] = datetime.strptime(json.get('authored_date'), '%Y-%m-%d').date()
        else:
            vals['authored_date'] = None

        bestsellers = [Bestseller.from_json(bestseller) for bestseller in json.get('bestsellers')]
        vals['num_bestsellers'] = len(bestsellers)

        bestseller_list = BestsellerList.create(**vals)

        for index, bestseller in enumerate(bestsellers):
            BestsellerListOrdering.create(
                index=index + 1, bestseller=bestseller, bestseller_list=bestseller_list)

        return bestseller_list


class Bestseller(BaseModel):
    author = ForeignKeyField(model=Author, null=True, on_delete='SET NULL')
    authored_date = DateField(null=True)
    description = TextField(null=True)
    title = TextField()

    @classmethod
    def search(cls, search_str, max_results=25, page=1):
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

    @classmethod
    def from_json(cls, json):
        json['author'] = Author.get_or_create(name=json.get('author'))[0]
        return Bestseller.create(**json)


class BestsellerListOrdering(BaseModel):
    bestseller_list = ForeignKeyField(model=BestsellerList, on_delete='CASCADE')
    bestseller = ForeignKeyField(model=Bestseller, on_delete='CASCADE')
    index = IntegerField()


class File(BaseModel):
    bestseller_list = ForeignKeyField(model=BestsellerList, on_delete='CASCADE')
    name = TextField()
    path = TextField()
    expire_time = DateTimeField(null=True, default=datetime.now() + timedelta(hours=1))

    # MAX_IMAGE_SIZE = 256
    # MAX_FILE_SIZE = 1024

    @classmethod
    def remove_unaccounted(cls):
        db_paths = {f.path: f for f in File.select()}
        local_paths = list(glob('./googleplex/uploaded/*'))
        to_delete = []

        for path in local_paths:
            if not path in db_paths.keys():
                to_delete.append(path)
                local_paths.remove(path)

        for path, f in db_paths.items():
            if not path in local_paths:
                f.delete_instance()

        for path in to_delete:
            os.remove(path)

    @classmethod
    def remove_expired(cls):
        for f in File.select().where(File.expire_time < datetime.now()):
            f.delete_instance()

    @classmethod
    def upload(cls, file_obj, bestseller_list):
        File.remove_expired()

        if not os.path.isdir('./googleplex/uploaded'):
            os.mkdir('./googleplex/uploaded')

        path = './googleplex/uploaded/%d-%s' % (bestseller_list.id, file_obj.name)
        with open(path, 'wb+') as f:
            f.write(file_obj.body)

        return File.create(path=path, name=file_obj.name, bestseller_list=bestseller_list)

    @property
    def is_image(self):
        return imghdr.what(self.path) is not None


class Message(BaseModel):
    recipient = ForeignKeyField(null=True, model=User, on_delete='SET NULL')
    send_time = TextField()
    sender = ForeignKeyField(null=True, model=User, on_delete='SET NULL')
    subject = TextField()
    text = TextField()

    @classmethod
    def remove_floating(cls):
        for msg in Message.select().where(Message.recipient == None and Message.sender == None):
            msg.delete_instance()


class Search(BaseModel):
    saved_on = DateTimeField()
    comment = TextField()
    search_str = TextField()
    user = ForeignKeyField(model=User, on_delete='CASCADE')


class Session(BaseModel):
    expire_time = DateTimeField()
    uuid = TextField()
    user = ForeignKeyField(model=User, on_delete='CASCADE')

    @classmethod
    def for_user(cls, user_id, long_term=False):
        expire_t = datetime.now() + timedelta(hours=(72 if long_term else 1))
        return cls.create(expire_time=expire_t, uuid=str(uuid4()), user_id=user_id)

    def __str__(self):
        return '%s %s' % (self.user.id, self.uuid)

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
    bestseller_list = ForeignKeyField(model=BestsellerList, on_delete='CASCADE')
    tag = ForeignKeyField(model=Tag, on_delete='CASCADE')


class ActiveLink(BaseModel):
    link = TextField()
    action = TextField()
    user = ForeignKeyField(model=User, on_delete='CASCADE')
    expire_time = DateTimeField()

    VALID_ACTIONS = ['reset password', 'activate account']

    @classmethod
    def setup_link(cls, user, action):
        if action not in ActiveLink.VALID_ACTIONS:
            raise ValueError("The action '%s' is not valid" % action)

        else:
            link = gen_string(25)
            expire_time = datetime.now() + timedelta(days=1)
            active_link = ActiveLink.create(user=user, action=action,
                                            link=link, expire_time=expire_time)

            if action == 'reset password':
                email = write_email('reset_password.html', user, active_link)
                send_email(user.email, 'Reset Your Password', email)
                message = 'You have been sent an email with a link to reset your password!'

            elif action == 'activate account':
                email = write_email('activate_account.html', user, active_link)
                send_email(user.email, 'Activate Your Account', email)
                message = 'You have been sent an email to activate your account!'

            return message

    def activate(self):
        if self.expire_time >= datetime.now():
            if self.action == 'reset password':
                pass

            elif self.action == 'activate account':
                self.user.active = True
                self.user.save()

        self.delete_instance()


MODELS = [Author, User, Bestseller, BestsellerList, BestsellerListOrdering,
          File, Message, Search, Session, Tag, TagBestsellerListJunction, ActiveLink]

database.create_tables(MODELS, safe=True)
