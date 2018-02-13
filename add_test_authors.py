from googleplex import models

author_data = {
    "name" : "J. K. Rowling"
}

models.Author.create(**author_data)

author_data = {
    "name" : "Paulo Coelho"
}

models.Author.create(**author_data)
