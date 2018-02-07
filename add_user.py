from googleplex import models

user_data = {
    'admin': True,
    'email': 'abc@gmail.com',
    'first_name': 'George',
    'institution': 'Georgia Tech',
    'is_banned': False,
    'last_name': 'Burdell',
    'pass_hash': 'ABCDEFG',
    'position': 'Living Legend',
    'premium': True
}

models.User.create(**user_data)
