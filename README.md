Bestseller Archive
==================

This is the repository for Team 7321's Junior Design bestseller archiving
website built for Professor Rebekah Fitzsimmons of Georgia Tech.


### Installation / Customization
To run the archive, you will need
[python 3.6+](https://www.python.org/downloads/release/python-364/)
and [PostgreSQL](https://www.postgresql.org/download/) installed.

Once you clone the repo, make sure to run `pip3.6 install -r requirements.txt`
in the same directory as the [requirements.txt](./requirements.txt) file to
make sure all python module dependencies are installed on your device.

For the archive to run, certain variables need to be set, and our chosen format
is [.env](https://github.com/theskumar/python-dotenv), a style of setting
environment variables in a hidden file, rather than system-wide. Create a file
titled `.env` in the [googleplex](./googleplex/) directory of this project and
set the following variables in the style detailed on the
[.env](https://github.com/theskumar/python-dotenv) page:

```python
DB_USER="The database username"
DB_NAME="The database schema name"
DB_PASS="The database password"
DB_HOST="The database hostname"
SESSION_COOKIE_SECRET_KEY="A random key for securing session cookies"
EMAIL_USER="The username of the account to send emails with"
EMAIL_PASS="The corresponding email password"
```

The server and the `drop_tables.sh` script will use the variables set in the
`.env` file to perform operations. Make sure there are no spaces between
the variable names, the equals signs, and their values.


### Usage

To set up test data, you can run `python3.6 add_test_data.py`, and you can
reset the data by resetting the tables with `sh drop_tables.sh`.

To start the website, run `python3.6 run.py` in the root of the repo.
Navigate to http://localhost:5000 in any browser while it is running to
use the prototype.
