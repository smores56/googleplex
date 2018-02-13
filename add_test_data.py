from googleplex import models

user_data = {
    'admin': True,
    'email': 'gpurdell@gatech.edu',
    'first_name': 'George',
    'institution': 'Georgia Tech',
    'is_banned': False,
    'last_name': 'Burdell',
    'pass_hash': '9bb12650f91df864a09588e397327c26c20cc348f3d32847684971830828637e',
    'position': 'Living Legend',
    'premium': True
}

models.User.create(**user_data)
