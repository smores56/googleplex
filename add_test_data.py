from datetime import datetime
from googleplex import models


for model in [models.User, models.Bestseller, models.BestsellerList, models.Author]:
    model.delete().execute()


fields = [models.Author.name]
author_data = [
    {"name": "J. K. Rowling"},
    {"name": "Paulo Coelho"}
]

models.Author.insert_many(author_data, fields=fields)


b_list = models.BestsellerList
fields = [b_list.author, b_list.authored_date, b_list.contributor, b_list.description,
          b_list.num_bestsellers, b_list.submission_date, b_list.title]
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
        "author": None,
        "authored_date": None,
        "contributor": None,
        "description": None,
        "num_bestsellers": 10,
        "submission_date": datetime.now(),
        "title": "Asdf List"
    }
]

models.BestsellerList.insert_many(list_data, fields=fields)


fields = [models.Bestseller.title, models.Bestseller.bestseller_list]
book_data = [
    {"title": "Please Ignore", "bestseller_list": 3},
    {"title": "Test Book", "bestseller_list": 2}
]

models.Bestseller.insert_many(book_data, fields=fields)


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
