import json
from datetime import datetime
from datetime import timedelta

import pytest
from lesoon_common.test import UnittestBase
from tests.dbengine.alchemy.models import Book
from tests.dbengine.alchemy.models import BookFactory
from tests.dbengine.alchemy.models import BookSchema

from lesoon_restful.api import Api
from lesoon_restful.dbengine.alchemy import SQLAlchemyService
from lesoon_restful.resource import ModelResource


class TestFilters(UnittestBase):

    @pytest.fixture(autouse=True)
    def setup_method(self, app):

        class BookResource(ModelResource):

            class Meta:
                model = Book
                schema = BookSchema
                service = SQLAlchemyService

        api = Api(app)
        api.add_resource(BookResource)
        self.client = app.test_client(load_response=True)

        self.schema = BookSchema(many=True)
        self.books = [
            BookFactory(title='Game of Thrones',
                        year_published=1,
                        rating=5,
                        create_time=datetime.now()),
            BookFactory(title='The Kite Runner',
                        year_published=1,
                        rating=4,
                        create_time=datetime.now() - timedelta(days=1)),
            BookFactory(title='Doraemon',
                        year_published=3,
                        rating=3,
                        create_time=datetime.now() - timedelta(days=2)),
            BookFactory(title='Brother',
                        year_published=4,
                        rating=2,
                        create_time=datetime.now() - timedelta(days=3)),
            BookFactory(title='Being Alive',
                        year_published=5,
                        rating=1,
                        create_time=datetime.now() - timedelta(days=4)),
        ]

    def test_eq(self):
        where = {'title': 'Game of Thrones'}
        response = self.client.get(f'/book?where={json.dumps(where)}')
        assert response.result == self.schema.dump(self.books[:1])

        where = {'year_published': 1}
        response = self.client.get(f'/book?where={json.dumps(where)}')
        assert response.result == self.schema.dump(self.books[:2])

        where = {'title': 'The Kite Runner', 'year_published': 1}
        response = self.client.get(f'/book?where={json.dumps(where)}')
        assert response.result == self.schema.dump(self.books[1:2])

    def test_ne(self):
        where = {'title': {'$ne': 'Game of Thrones'}}
        response = self.client.get(f'/book?where={json.dumps(where)}')
        assert response.result == self.schema.dump(self.books[1:])

        where = {
            'title': {
                '$ne': 'Game of Thrones'
            },
            'year_published': {
                '$ne': 1
            }
        }
        response = self.client.get(f'/book?where={json.dumps(where)}')
        assert response.result == self.schema.dump(self.books[2:])

    def test_lt(self):
        where = {'rating': {'$lt': 5}}
        response = self.client.get(f'/book?where={json.dumps(where)}')
        assert response.result == self.schema.dump(self.books[1:])

        where = {'rating': {'$lt': 5}, 'year_published': {'$lt': 3}}
        response = self.client.get(f'/book?where={json.dumps(where)}')
        assert response.result == self.schema.dump(self.books[1:2])

    def test_lte(self):
        where = {'rating': {'$lte': 4}}
        response = self.client.get(f'/book?where={json.dumps(where)}')
        assert response.result == self.schema.dump(self.books[1:])

        where = {'rating': {'$lt': 4}, 'year_published': {'$lt': 3}}
        response = self.client.get(f'/book?where={json.dumps(where)}')
        assert response.result is None

    def test_gt(self):
        where = {'rating': {'$gt': 3}}
        response = self.client.get(f'/book?where={json.dumps(where)}')
        assert response.result == self.schema.dump(self.books[:2])

        where = {'rating': {'$gt': 2}, 'year_published': {'$gt': 1}}
        response = self.client.get(f'/book?where={json.dumps(where)}')
        assert response.result == self.schema.dump(self.books[2:3])

    def test_gte(self):
        where = {'rating': {'$gte': 3}}
        response = self.client.get(f'/book?where={json.dumps(where)}')
        assert response.result == self.schema.dump(self.books[:3])

        where = {'rating': {'$gte': 3}, 'year_published': {'$gte': 2}}
        response = self.client.get(f'/book?where={json.dumps(where)}')
        assert response.result == self.schema.dump(self.books[2:3])

    def test_in(self):
        where = {'rating': {'$in': [1, 2, 3]}}
        response = self.client.get(f'/book?where={json.dumps(where)}')
        assert response.result == self.schema.dump(self.books[2:])

        where = {
            'rating': {
                '$in': [1, 2, 3]
            },
            'year_published': {
                '$in': [3, 4]
            }
        }
        response = self.client.get(f'/book?where={json.dumps(where)}')
        assert response.result == self.schema.dump(self.books[2:4])

    def test_contains(self):
        where = {'title': {'$contains': 'B'}}
        response = self.client.get(f'/book?where={json.dumps(where)}')
        assert response.result == self.schema.dump(self.books[3:])

    def test_startswith(self):
        where = {'title': {'$startswith': 'Game'}}
        response = self.client.get(f'/book?where={json.dumps(where)}')
        assert response.result == self.schema.dump([self.books[0]])

    def test_endswith(self):
        where = {'title': {'$endswith': 'Alive'}}
        response = self.client.get(f'/book?where={json.dumps(where)}')
        assert response.result == self.schema.dump([self.books[4]])

    def test_between(self):
        start_time = (datetime.now() -
                      timedelta(days=2)).strftime('%Y-%m-%d 00:00:00')
        end_time = datetime.now().strftime('%Y-%m-%d 00:00:00')
        where = {'create_time': {'$between': [start_time, end_time]}}
        response = self.client.get(f'/book?where={json.dumps(where)}')
        assert response.result == self.schema.dump(self.books[1:3])
