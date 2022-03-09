import random
from datetime import datetime

from lesoon_common.extensions import mg
from lesoon_common.test import ft
from lesoon_common.test import SqlaFatory
from marshmallow_mongoengine.schema import ModelSchema


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.Integer, default=1)


class AuthorSchema(SQLAlchemyAutoSchema):

    class Meta(SQLAlchemyAutoSchema.Meta):
        model = Author


class AuthorFactory(ModelSchema):
    id = ft.Sequence(lambda n: n + 1)
    name = ft.Faker('word')
    age = ft.LazyFunction(lambda: random.randint(0, 100))
    gender = ft.LazyFunction(lambda: random.randint(0, 1))

    class Meta:
        model = Author


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(), nullable=False)
    year_published = db.Column(db.Integer)
    rating = db.Column(db.Integer, default=5)
    author_id = db.Column(db.Integer)
    create_time = db.Column(db.DateTime, default=datetime.now)


class BookSchema(ModelSchema):

    class Meta(ModelSchema.Meta):
        model = Book


class BookFactory(SqlaFatory):
    id = ft.Sequence(lambda n: n + 1)
    title = ft.Faker('word')
    year_published = ft.Faker('pyint', min_value=0, max_value=10)
    rating = ft.Faker('pyint', min_value=0, max_value=5)
    author_id = ft.Sequence(lambda n: n + 1)

    class Meta:
        model = Book
