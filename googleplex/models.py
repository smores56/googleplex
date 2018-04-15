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
        """
        A property to retrieve all of the bestsellers written by this Author.

        inputs:
            None

        outputs: A list of Bestsellers written by this Author
        """
        if not hasattr(self, '_books'):
            self._books = list(Bestseller.select().where(Bestseller.author == self))

        return self._books

    @property
    def age(self):
        """
        A property giving the age of this Author. If the Author has a `birth_date`, their age
        if calculated as the difference between their `death_date` if they have one or the
        current date it they don't and their `birth_date`, otherwise it is None.

        inputs:
            None

        output: An int value representing this Author's age
        """
        # Using the `_age` attribute to avoid recalculation
        if not hasattr(self, '_age'):
            if self.birth_date:
                end_date = self.death_date or date.today()
                end_bday = date(end_date.year, self.birth_date.month, self.birth_date.day)

                self._age = end_date.year - self.birth_date.year
                # A trick to fix the case when birthdays are after the "end date"
                if end_bday > end_date:
                    self._age -= 1

            else:
                self._age = None

        return self._age

    @classmethod
    def search(cls, search_str, max_results=25, page=1):
        """
        Searches for authors in the database.

        inputs:
            search_str: A string to search Author names with
            max_results=25: The max results per page
            page=1: The page of results to jump to

        output: A list of Authors with the `search_str` in their name
        """
        start = (page - 1) * max_results
        end = start + max_results
        # Finds all authors with `search_str` in their name
        authors = list(Author.select().where(Author.name.contains(search_str)))

        return {
            # The results requested
            'results': list(itertools.islice(authors, start, end)),
            # The total number of search results
            'num_results': len(authors),
            # The index of the first search result returned
            'start': start,
            # The index of the last search result returned
            'end': end
        }

    @classmethod
    def get_author(cls, author_name):
        """
        Finds an author in the database with the given name. Returns None if no Author is found.

        inputs:
            author_name: The exact name of the Author in the system

        output: An Author, or None
        """
        return Author.get_or_none(Author.name == author_name)


class User(BaseModel):
    admin = BooleanField(default=False)  # Whether the user is an administrator
    email = TextField(unique=True)
    first_name = TextField()
    institution = TextField(null=True)  # The institution the user is from
    banned = BooleanField(default=False)  # Whether the user has been banned
    last_name = TextField()
    pass_hash = TextField()  # A double-hashed (via scrypt) string of the user's password
    position = TextField(null=True)  # The user's position in their institute
    premium = BooleanField(default=False)  # Whether the user has a premium account (not used yet)
    active = BooleanField(default=False)  # Whether the user is active / can log in

    @property
    def full_name(self):
        """
        A property for the full name of this User.

        inputs:
            None

        output: A string representing the User's full name
        """
        return "%s %s" % (self.first_name, self.last_name)

    @classmethod
    def load_if_logged_in(cls, request):
        """
        Loads the User if they are currently logged in to the system.

        inputs:
            request: The web request to take cookies from.

        output: The User if they are logged in, or None
        """
        login_cookie = request.cookies.get('login_cookie')
        # If the user has a login cookie,
        if login_cookie:
            # Try to find a live login session tied to their account
            session = Session.from_cookie(login_cookie)
            if session:
                # If they are logged in, refresh the expire time of their login session
                session.refresh()
                # and return their account's model
                return session.user

            else:
                # If they have a bad login cookie, delete it
                del request.cookies['login_cookie']

        # In any case of failure, return None as they aren't logged in
        return None

    @classmethod
    def register(cls, form, premium=False, admin=False):
        """
        Registers a new User.

        inputs:
            form: The dictionary with fields from the registration page.

        output: Either (The registered User, None) or (None, "an error string")
        """
        vals = {}
        # The below fields are the required ones. If they are missing, return an error
        # describing what failure occurred
        for field, field_name in [('email', 'Email'), ('first_name', 'First name'),
                                  ('last_name', 'Last name'), ('pass_hash', 'Password')]:
            val = form.get(field, None)
            if val is None:
                return (None, field_name + ' not specified.')
            else:
                vals[field] = val

        # These fields are optional, so they default to None if they aren't found on the form
        for opt_field in ['institution', 'position']:
            vals[opt_field] = form.get(opt_field, None)

        # The following fields are privileges when creating the account
        vals.update({'premium': premium, 'admin': admin, 'banned': False})
        # The given password hash is rehashed for security purposes
        re_hash = scrypt(vals['pass_hash'], (vals['email'] + 'xyz')[:8])
        vals['pass_hash'] = re_hash

        # If an account with the same email already exists, return an error message.
        if User.get_or_none(User.email == vals['email']) is not None:
            return (None, 'A user with the same email already exists.')

        # Try to create the user, and on failure, return an error describing the failure
        try:
            user = User.create(**vals)
            return (user, None)

        except DoesNotExist as e:
            return (None, 'An unknown error occurred: %s' % e)


class BestsellerList(BaseModel):
    author = ForeignKeyField(null=True, model=Author, on_delete='SET NULL')
    authored_date = DateField(null=True)
    # User that contributed this BestsellerList
    contributor = ForeignKeyField(null=True, model=User, on_delete='SET NULL')
    description = TextField(null=True)
    num_bestsellers = IntegerField()
    submission_date = DateField()
    title = TextField()

    @property
    def bestsellers(self):
        """
        Gets the Bestsellers in this list in the correct order.

        inputs:
            None

        output: A list of BestsellerLists
        """
        return [ordering.bestseller for ordering in BestsellerListOrdering.select().where(
            BestsellerListOrdering.bestseller_list == self).order_by(BestsellerListOrdering.index)]

    @property
    def tags(self):
        """
        Gets the Tags of this BestsellerList

        inputs:
            None

        output: A list of Tags
        """
        return [j.tag for j in TagBestsellerListJunction.select()
                .where(TagBestsellerListJunction.bestseller_list == self)]

    @classmethod
    def search(cls, search_str, max_results=25, page=1):
        """
        Searches for BestsellerLists in the database.

        inputs:
            search_str: A string to search BestsellerList titles with
            max_results=25: The max results per page
            page=1: The page of results to jump to

        output: A list of BestsellerLists with the `search_str` in their title
        """
        start = (page - 1) * max_results
        end = start + max_results
        lists = list(BestsellerList.select().where(BestsellerList.title.contains(search_str)))

        return {
            # The results requested
            'results': list(itertools.islice(lists, start, end)),
            # The total number of search results
            'num_results': len(lists),
            # The index of the first search result returned
            'start': start,
            # The index of the last search result returned
            'end': end
        }

    @classmethod
    def get_list(cls, list_title, list_id):
        """
        Finds a BestsellerList with the same title and id.

        inputs:
            list_title: The exact title of a BestsellerList
            list_id: The exact id of a BestsellerList

        output: A matching BestsellerList, or None
        """
        return BestsellerList.get_or_none((BestsellerList.title == list_title) and
                                          (BestsellerList.id == list_id))

    @classmethod
    def from_form(cls, form, user=None):
        """
        Builds a new BestsellerList from a parsed HTML form.

        inputs:
            form: The dictionary of values to construct this list from.
            user=None: The user the attribute this list to.

        output: the new BestsellerList
        """
        vals = {'contributor': user, 'submission_date': date.today()}
        vals['title'] = form.get('title')
        vals['num_bestsellers'] = form.get('num_bestsellers')

        if 'description' in form:
            vals['description'] = form.get('description')
        # If an `authored_date` is provided,
        if 'authored_date' in form:
            # parse the date from the form and add the date object to the BestsellerList
            vals['authored_date'] = datetime.strptime(form['authored_date'][0], '%Y-%m-%d').date()
        if 'author' in form:
            vals['author'] = Author.get_or_create(name=form.get('author'))[0]

        return BestsellerList.create(**vals)

    @classmethod
    def from_json(cls, json, user=None):
        """
        Builds a new BestsellerList from a parsed JSON request.

        inputs:
            json: The dictionary of values to construct this list from.
            user=None: The user the attribute this list to.

        output: the new BestsellerList
        """
        vals = {'contributor': user, 'submission_date': date.today(),
                'active': False, 'title': json.get('title'),
                'description': json.get('description') if 'description' in json else None}
        if 'author' in json:
            vals['author'] = Author.get_or_create(name=json.get('author'))[0]
        else:
            vals['author'] = None
        if 'authored_date' in json:
            # The same as in from_form()
            vals['authored_date'] = datetime.strptime(json.get('authored_date'), '%Y-%m-%d').date()
        else:
            vals['authored_date'] = None

        bestsellers = [Bestseller.from_json(bestseller) for bestseller in json.get('bestsellers')]
        vals['num_bestsellers'] = len(bestsellers)

        bestseller_list = BestsellerList.create(**vals)

        # Create the orderings of the bestsellers for indexing later
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
        """
        Searches for Bestellers in the database.

        inputs:
            search_str: A string to search Bestseller names with
            max_results=25: The max results per page
            page=1: The page of results to jump to

        output: A list of Bestellers with the `search_str` in their title
        """
        start = (page - 1) * max_results
        end = start + max_results
        bestsellers = list(Bestseller.select().where(Bestseller.title.contains(search_str)))

        return {
            # The results requested
            'results': list(itertools.islice(bestsellers, start, end)),
            # The total number of search results
            'num_results': len(bestsellers),
            # The index of the first search result returned
            'start': start,
            # The index of the last search result returned
            'end': end
        }

    @classmethod
    def get_book(cls, book_title, book_id):
        """
        Finds a Bestseller in the system based on its title and id.

        inputs:
            book_title: The exact title of the book
            book_id: The numeric id of the book

        output: The matching Bestseller, or None
        """
        return Bestseller.get_or_none((Bestseller.title == book_title) and
                                      (Bestseller.id == book_id))

    def get_lists_with_this_bestseller(self):
        """
        Finds all BestsellerLists that reference this Bestseller

        inputs:
            None

        output: a list of BestsellerLists
        """
        return [ordering.bestseller_list for ordering in
                BestsellerListOrdering.select().where(BestsellerListOrdering.bestseller == self)]

    @classmethod
    def from_json(cls, json):
        """
        Creates a new Bestseller from a dictionary

        inputs:
            json:
                A dictionary with values from a JSON request from the website

        output: The matching Bestseller
        """
        # Get the first element of get_or_create() as it returns a tuple based on success
        json['author'] = Author.get_or_create(name=json.get('author'))[0]
        return Bestseller.create(**json)


class BestsellerListOrdering(BaseModel):
    # A class for keeping the order of Bestsellers in BestsellerLists
    bestseller_list = ForeignKeyField(model=BestsellerList, on_delete='CASCADE')
    bestseller = ForeignKeyField(model=Bestseller, on_delete='CASCADE')
    index = IntegerField()

    @classmethod
    def clear_list(cls, bestseller_list):
        """
        Disassociates all Bestsellers from a BestsellerList

        inputs:
            bestseller_list: The BestsellerList to clear

        output: None
        """
        BestsellerListOrdering.delete().where(BestsellerListOrdering.bestseller_list == bestseller_list).execute()


class File(BaseModel):
    bestseller_list = ForeignKeyField(model=BestsellerList, on_delete='CASCADE')
    name = TextField()
    path = TextField()
    expire_time = DateTimeField(null=True, default=datetime.now() + timedelta(hours=1))

    @classmethod
    def remove_unaccounted(cls):
        """
        Removes all File models that don't have a file on the disk and vice versa.

        inputs:
            None

        output: None
        """
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
        """
        Removes all Files that have passed their expire_time.

        inputs:
            None

        output: None
        """
        for f in File.select().where(File.expire_time < datetime.now()):
            f.delete_instance()

    @classmethod
    def upload(cls, file_obj, bestseller_list):
        """
        Uploads a new file to the disk and creates a database counterpart.

        inputs:
            file_obj: The file sent in the request
            bestseller_list: the BestsellerList that this File corresponds to

        output: The newly create File
        """
        if not os.path.isdir('./googleplex/uploaded'):
            os.mkdir('./googleplex/uploaded')

        path = './googleplex/uploaded/%d-%s' % (bestseller_list.id, file_obj.name)
        with open(path, 'wb+') as f:
            f.write(file_obj.body)

        return File.create(path=path, name=file_obj.name, bestseller_list=bestseller_list)

    @property
    def is_image(self):
        """
        Checks whether the associated file on the disk is an image

        inputs:
            None

        output: Whether the associated file is an image
        """
        return imghdr.what(self.path) is not None


class Message(BaseModel):
    # A currently unused class for sending messages between Users.
    recipient = ForeignKeyField(null=True, model=User, on_delete='SET NULL')
    send_time = TextField()
    sender = ForeignKeyField(null=True, model=User, on_delete='SET NULL')
    subject = TextField()
    text = TextField()

    @classmethod
    def remove_floating(cls):
        """
        Removes all messages that have neither a sender or a recipient

        inputs:
            None

        output: None
        """
        for msg in Message.select().where(Message.recipient == None and Message.sender == None):
            msg.delete_instance()


class Search(BaseModel):
    # A currently unused class for saving searches to a User's account
    saved_on = DateTimeField()
    comment = TextField()
    search_str = TextField()
    user = ForeignKeyField(model=User, on_delete='CASCADE')


class Session(BaseModel):
    expire_time = DateTimeField()
    uuid = TextField()  # A random string for secure identification of session cookies.
    user = ForeignKeyField(model=User, on_delete='CASCADE')

    @classmethod
    def for_user(cls, user_id, long_term=False):
        """
        Builds a new Session for a User logging in

        inputs:
            user_id: The id of the User to make a session for
            long_term=False: Whether the session expires in 72 hours or 1 hour

        output: the new Session
        """
        expire_t = datetime.now() + timedelta(hours=(72 if long_term else 1))
        return cls.create(expire_time=expire_t, uuid=str(uuid4()), user_id=user_id)

    def __str__(self):
        return '%s %s' % (self.user.id, self.uuid)

    @classmethod
    def remove_expired(cls):
        """
        Removes Sessions that passed their `expire_time`

        inputs:
            None

        output: None
        """
        Session.delete().where(cls.expire_time < datetime.now()).execute()

    def refresh(self):
        """
        Refreshes this Session if it isn't expired to an hour from now

        inputs:
            None

        output: None
        """
        now = datetime.now()
        an_hour_from_now = now + timedelta(hours=1)
        if self.expire_time < an_hour_from_now:
            self.update(expire_time=an_hour_from_now).execute()

    def from_cookie(cookie):
        """
        Loads a User's Session if the given cookie is valid and not expired.

        inputs:
            cookie: The cookie string to parse and find a Session with

        output: The User's active Session, or None
        """
        if isinstance(cookie, str):
            user_id, uuid = cookie.split(' ')[:2]
            session = Session.get_or_none(user=user_id, uuid=uuid)

            if session:
                if session.expire_time < datetime.now():
                    session.delete_instance()

                else:
                    session.refresh()
                    return session

        return None


class Tag(BaseModel):
    name = TextField()


class TagBestsellerListJunction(BaseModel):
    # A class for tying together Tags and BestsellerLists in a many-to-many relationship
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
        """
        Sets up an ActiveLink to perform some action on a User's account

        inputs:
            user: The User to act on with this ActiveLink
            action: The action for the link to perform

        output: the message to return to the User upon setting up this ActiveLink
        """
        if action not in ActiveLink.VALID_ACTIONS:
            raise ValueError("The action '%s' is not valid" % action)

        else:
            # A random string of length 25
            link = gen_string(25)
            # The link expires in a day
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
        """
        Activates this Link, performing its action and then deleting it

        inputs:
            None

        output: None
        """
        if self.expire_time >= datetime.now():
            if self.action == 'reset password':
                pass

            elif self.action == 'activate account':
                self.user.active = True
                self.user.save()

        self.delete_instance()


MODELS = [Author, User, Bestseller, BestsellerList, BestsellerListOrdering,
          File, Message, Search, Session, Tag, TagBestsellerListJunction, ActiveLink]

# Creates all tables that don't yet exist on import
database.create_tables(MODELS, safe=True)
