from googleplex import models

book_data = {
    "title" : "Test Book"
}

models.Bestseller.create(**book_data)

book_data = {
    "title" : "Please Ignore"
}

models.Bestseller.create(**book_data)
