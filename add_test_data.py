from datetime import datetime
from googleplex import models


for model in [models.User, models.Bestseller, models.BestsellerList, models.Author]:
    model.delete().execute()


author_data = [
    {"name": "J. K. Rowling"},
    {"name": "Paulo Coelho"}
]

for a in author_data:
    models.Author.create(**a)


list_data = [
    {
        "author": None,
        "authored_date": None,
        "contributor": None,
        "description": None,
        "num_bestsellers": 10,
        "submission_date": datetime.now(),
        "title": "Test List"
    },
    {
        "author": models.Author.get(models.Author.name == 'Paulo Coelho'),
        "authored_date": None,
        "contributor": None,
        "description": None,
        "num_bestsellers": 10,
        "submission_date": datetime.now(),
        "title": "Asdf List"
    }
]

for l in list_data:
    models.BestsellerList.create(**l)


book_data = [
    {"title": "Please Ignore", "bestseller_list": models.BestsellerList.get(
        models.BestsellerList.title == 'Test List')},
    {"title": "Test Book", "bestseller_list": models.BestsellerList.get(
        models.BestsellerList.title == 'Asdf List')}
]

for b in book_data:
    models.Bestseller.create(**b)


user_data = {
    'admin': True,
    'email': 'gburdell@gatech.edu',
    'first_name': 'George',
    'institution': 'Georgia Tech',
    'is_banned': False,
    'last_name': 'Burdell',
    'pass_hash': '8cdcca28a063f17be8476b8d899aa22cf9593dbd5db4b23a6d93d2a00b0c2295',
    'position': 'Living Legend',
    'premium': True
}

models.User.create(**user_data)
