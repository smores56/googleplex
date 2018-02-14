from googleplex import models

book_data = {
    "title" : "Test Book",
    "bestseller_list" : 2
}

models.Bestseller.create(**book_data)

book_data = {
    "title" : "Please Ignore",
    "bestseller_list" : 3
}

models.Bestseller.create(**book_data)
