CREATE EXTENSION hstore;

CREATE TABLE files (
    id          serial PRIMARY KEY,
    list_id     integer NOT NULL REFERENCES lists ON DELETE CASCADE,
    name        text NOT NULL,
    path        text NOT NULL,
);

CREATE TABLE users (
    id           serial PRIMARY KEY,
    email        text NOT NULL UNIQUE,
    pass_hash    text NOT NULL,
    first_name   text NOT NULL,
    last_name    text NOT NULL,
    institution  text NOT NULL,
    -- phone_number varchar(10) NOT NULL,   DO WE NEED THIS?
    premium      boolean NOT NULL DEFAULT 'f',
    admin        boolean NOT NULL DEFAULT 'f'
);

CREATE TABLE lists (
    id               serial PRIMARY KEY,
    contributor_id   integer REFERENCES users ON DELETE SET NULL,
    title            text NOT NULL,
    author           text NOT NULL,
    description      text NOT NULL,
    num_bestsellers  integer NOT NULL
);

CREATE TABLE bestsellers (
    id          serial PRIMARY KEY,
    list_id     integer NOT NULL REFERENCES lists ON DELETE CASCADE,
    title       text NOT NULL,
    author      text NOT NULL,
    description text NOT NULL,
    links       hstore -- a key / value datatype for storing link names and paths
);

CREATE TABLE reviews (
    id          serial PRIMARY KEY,
    list_id     integer NOT NULL REFERENCES lists ON DELETE CASCADE,
    user_id     integer REFERENCES users ON DELETE SET NULL,
);

CREATE TABLE searches (
    id         serial PRIMARY KEY,
    user_id    integer REFERENCES users ON DELETE CASCADE,
    saved_on   datetime NOT NULL,
    search_str text NOT NULL
);

CREATE TABLE sessions (
    id          serial PRIMARY KEY,
    user_id     integer NOT NULL REFERENCES users ON DELETE CASCADE,
    random_int  integer NOT NULL,
    expire_time datetime NOT NULL
);

CREATE TABLE messages (
    id           serial PRIMARY KEY,
    sender_id    integer REFERENCES users ON DELETE SET NULL,
    recipient_id integer REFERENCES users ON DELETE SET NULL,
    send_time    text NOT NULL,
    subject      text NOT NULL,
    text         text NOT NULL
);
