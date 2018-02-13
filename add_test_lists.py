from googleplex import models
import datetime

submission_date = datetime.datetime.now()

list_data = {
    "author" : None,
    "authored_date" : None,
    "contributor" : None,
    "description" : None,
    "num_bestsellers" : 10,
    "submission_date" : submission_date,
    "title" : "Test List"
}

models.BestsellerList.create(**list_data)

submission_date = datetime.datetime.now()

list_data = {
    "author" : None,
    "authored_date" : None,
    "contributor" : None,
    "description" : None,
    "num_bestsellers" : 10,
    "submission_date" : submission_date,
    "title" : "Asdf List"
}

models.BestsellerList.create(**list_data)
