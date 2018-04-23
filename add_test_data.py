#!/usr/bin/python3

from datetime import datetime
from googleplex import models

for model in [models.User, models.Bestseller, models.BestsellerList, models.Author,
              models.BestsellerListOrdering, models.Tag, models.TagBestsellerListJunction]:
    model.delete().execute()

user_data = {
    'admin': True,
    'email': 'gburdell@gatech.edu',
    'first_name': 'George',
    'institution': 'Georgia Tech',
    'is_banned': False,
    'last_name': 'Burdell',
    'pass_hash': '8cdcca28a063f17be8476b8d899aa22cf9593dbd5db4b23a6d93d2a00b0c2295',
    'position': 'Living Legend',
    'premium': True,
    'active': True
}

models.User.create(**user_data)

rowling_birth = datetime.strptime('07311965', '%m%d%Y')
coelho_birth = datetime.strptime('08241947', '%m%d%Y')
shakespeare_birth = datetime.strptime('01011564', '%m%d%Y')
shakespeare_death = datetime.strptime('04231616', '%m%d%Y')

author_data = [
    {'name': 'J. K. Rowling', 'birth_date': rowling_birth},
    {'name': 'Paulo Coelho', 'birth_date': coelho_birth},
    {'name': 'William Shakespeare', 'birth_date': shakespeare_birth, 'death_date': shakespeare_death}
]

for a in author_data:
    models.Author.create(**a)


list_data = [
    {
        'author': None,
        'authored_date': None,
        'contributor': models.User.get(models.User.email == 'gburdell@gatech.edu'),
        'description': 'Lorem ipsum latin stuff',
        'num_bestsellers': 10,
        'submission_date': datetime.now(),
        'title': 'Test List'
    },
    {
        'author': models.Author.get(models.Author.name == 'Paulo Coelho'),
        'authored_date': None,
        'contributor': None,
        'description': None,
        'num_bestsellers': 10,
        'submission_date': datetime.now(),
        'title': 'Asdf List'
    }
]

for l in list_data:
    models.BestsellerList.create(**l)


book_data = [
    {'title': 'Please Ignore',
     'contributor': models.User.get(),
     'author': models.Author.get(models.Author.name == 'Paulo Coelho'),
     'description': 'Lorem ipsum latin stuff'},
    {'title': 'Test Book'},
    {'title': 'Another Test',
     'author': models.Author.get(models.Author.name == 'J. K. Rowling')}
]

for b in book_data:
    models.Bestseller.create(**b)


ordering_data = [
    {'index': 1,
     'bestseller': models.Bestseller.get(models.Bestseller.title == 'Please Ignore'),
     'bestseller_list': models.BestsellerList.get(models.BestsellerList.title == 'Test List')},
    {'index': 2,
     'bestseller': models.Bestseller.get(models.Bestseller.title == 'Another Test'),
     'bestseller_list': models.BestsellerList.get(models.BestsellerList.title == 'Test List')},
    {'index': 3,
     'bestseller': models.Bestseller.get(models.Bestseller.title == 'Test Book'),
     'bestseller_list': models.BestsellerList.get(models.BestsellerList.title == 'Test List')},
    {'index': 1,
     'bestseller': models.Bestseller.get(models.Bestseller.title == 'Another Test'),
     'bestseller_list': models.BestsellerList.get(models.BestsellerList.title == 'Asdf List')}
]

for o in ordering_data:
    models.BestsellerListOrdering.create(**o)


tag_data = [
    {'name': 'Short'},
    {'name': 'Trustworthy'},
    {'name': 'Informative'},
    {'name': 'Modern'},
    {'name': 'Tech-Related'},
]

for t in tag_data:
    models.Tag.create(**t)


junction_data = [
    {'tag': models.Tag.get(models.Tag.name == 'Short'),
     'bestseller_list': models.BestsellerList.get(models.BestsellerList.title == 'Test List')},
    {'tag': models.Tag.get(models.Tag.name == 'Trustworthy'),
     'bestseller_list': models.BestsellerList.get(models.BestsellerList.title == 'Test List')},
    {'tag': models.Tag.get(models.Tag.name == 'Informative'),
     'bestseller_list': models.BestsellerList.get(models.BestsellerList.title == 'Test List')},
    {'tag': models.Tag.get(models.Tag.name == 'Short'),
     'bestseller_list': models.BestsellerList.get(models.BestsellerList.title == 'Test List')},
    {'tag': models.Tag.get(models.Tag.name == 'Modern'),
     'bestseller_list': models.BestsellerList.get(models.BestsellerList.title == 'Asdf List')},
    {'tag': models.Tag.get(models.Tag.name == 'Tech-Related'),
     'bestseller_list': models.BestsellerList.get(models.BestsellerList.title == 'Asdf List')}
]

for j in junction_data:
    models.TagBestsellerListJunction.create(**j)
