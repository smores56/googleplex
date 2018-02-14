CREATE EXTENSION hstore;

CREATE TABLE users (
    id          serial PRIMARY KEY,
    email       text NOT NULL UNIQUE,
    pass_hash   text NOT NULL,
    first_name  text NOT NULL,
    last_name   text NOT NULL,
    position    text,
    institution text,
    premium     boolean NOT NULL DEFAULT 'f',
    admin       boolean NOT NULL DEFAULT 'f',
    is_banned   boolean NOT NULL DEFAULT 'f'
);

CREATE TABLE authors (
    id             serial PRIMARY KEY,
    name           text NOT NULL,
    birth_date     date,
    death_date     date,
    ethnicity      text
    -- ADD MORE FIELDS IN THE FUTURE?
);

CREATE TABLE bestseller_lists (
    id              serial PRIMARY KEY,
    contributor_id  integer REFERENCES users ON DELETE SET NULL,
    title           text NOT NULL,
    author_id       integer REFERENCES authors ON DELETE SET NULL,
    description     text,
    num_bestsellers integer NOT NULL DEFAULT '1',
    authored_date   date,
    submission_date date NOT NULL
);

CREATE TABLE bestsellers (
    id                 serial PRIMARY KEY,
    bestseller_list_id integer NOT NULL REFERENCES bestseller_lists ON DELETE CASCADE,
    title              text NOT NULL,
    author             text,
    description        text,
    links              hstore -- a key / value datatype for storing link names and paths
);

CREATE TABLE reviews (
    id                 serial PRIMARY KEY,
    bestseller_list_id integer NOT NULL REFERENCES bestseller_lists ON DELETE CASCADE,
    user_id            integer REFERENCES users ON DELETE SET NULL,
    rating             integer NOT NULL CHECK(rating >= 1 AND rating <= 5),
    authored_time      timestamp NOT NULL,
    text               text NOT NULL
);

CREATE TABLE files (
    id                 serial PRIMARY KEY,
    bestseller_list_id integer NOT NULL REFERENCES bestseller_lists ON DELETE CASCADE,
    name               text NOT NULL,
    path               text NOT NULL
);

CREATE TABLE searches (
    id         serial PRIMARY KEY,
    user_id    integer REFERENCES users ON DELETE CASCADE,
    saved_on   timestamp NOT NULL,
    search_str text NOT NULL
);

CREATE TABLE sessions (
    id          serial PRIMARY KEY,
    user_id     integer NOT NULL REFERENCES users ON DELETE CASCADE,
    uuid        text NOT NULL,
    expire_time timestamp NOT NULL
);

CREATE TABLE messages (
    id           serial PRIMARY KEY,
    sender_id    integer REFERENCES users ON DELETE SET NULL,
    recipient_id integer REFERENCES users ON DELETE SET NULL,
    send_time    text NOT NULL,
    subject      text NOT NULL,
    text         text NOT NULL
);

CREATE TABLE tags (
    id   serial PRIMARY KEY,
    name text NOT NULL
);

create table tag_bestseller_list_junction (
    tag_id             integer REFERENCES tags,
    bestseller_list_id integer REFERENCES bestseller_lists,
    constraint id PRIMARY KEY (tag_id, bestseller_list_id)
);
