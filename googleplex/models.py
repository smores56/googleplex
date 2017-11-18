import datetime


class BestsellerList:

    def __init__(self, name, bestsellers, author='Unknown', publication_date=None, tags=[]):
        self.name = name
        self.bestsellers = bestsellers
        self.size = len(bestsellers)
        self.author = author
        self.publication_date = publication_date
        self.tags = tags


class Bestseller:

    def __init__(self, name, author, reviews=[], publication_date=None, data=None):
        self.name = name
        self.author = author
        self.reviews = reviews
        self.publication_date = publication_date or 'Unknown'
        self.data = data or 'None'


class Review:

    def __init__(self, author, score, text):
        self.author = author
        self.score = score
        self.text = text
