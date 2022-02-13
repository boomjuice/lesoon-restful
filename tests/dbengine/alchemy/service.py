import pytest
from lesoon_common.test import ft
from lesoon_common.test import UnittestBase
from tests.dbengine.alchemy.models import Book
from tests.dbengine.alchemy.models import BookFactory
from tests.dbengine.alchemy.models import BookSchema

from lesoon_restful.dbengine.alchemy import SQLAlchemyService


class TestSQLAlchemyService(UnittestBase):

    @pytest.fixture(autouse=True)
    def setup_method(self):

        class BookService(SQLAlchemyService):

            class Meta:
                model = Book
                schema = BookSchema

        self.service = BookService()
        self.schema = BookSchema(many=True, exclude=('create_time',))

    def test_service(self):
        assert self.service.id_attribute == 'id'
        assert self.service.id_column == Book.id

    def test_create(self):
        books = ft.build_batch(dict, size=5, FACTORY_CLASS=BookFactory)
        self.service.create(books)
        assert self.schema.dump(Book.query.all()) == books

    def test_update(self):
        books = ft.build_batch(dict, size=5, FACTORY_CLASS=BookFactory)
        self.service.create(books)
        books[0]['rating'] = books[0]['rating'] + 1
        books[1]['year_published'] = books[1]['year_published'] + 1
        books[2]['title'] = '单元测试'
        self.service.update(books)
        assert self.schema.dump(Book.query.all()) == books

    def test_delete(self):
        books = ft.build_batch(dict, size=5, FACTORY_CLASS=BookFactory)
        self.service.create(books)
        book = books.pop()
        self.service.delete(ids=[book['id']])
        assert self.schema.dump(Book.query.all()) == books
