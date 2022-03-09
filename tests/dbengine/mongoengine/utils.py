import pytest
from lesoon_common.extensions import db
from lesoon_common.test import UnittestBase
from sqlalchemy.sql.expression import alias
from tests.dbengine.alchemy.models import Author
from tests.dbengine.alchemy.models import Book

from lesoon_restful.dbengine.alchemy.utils import parse_prefix_alias
from lesoon_restful.dbengine.alchemy.utils import parse_query_related_models
from lesoon_restful.exceptions import FilterInvalid


class TestUtils(UnittestBase):

    def test_parse_alias_match(self):
        a = alias(Book, name='a')
        r = parse_prefix_alias('a.id', a)
        assert r == 'id'

    def test_parse_alias_not_match(self):
        a = alias(Book, name='a')
        r = parse_prefix_alias('b.id', a)
        assert r is None

    def test_parse_alias_invalid_col(self):
        with pytest.raises(FilterInvalid):
            a = alias(Book, name='a')
            parse_prefix_alias('a.b.c', a)

    def test_parse_related_models_single(self):
        query = Book.query
        r = parse_query_related_models(query=query)
        assert len(r) == 1
        assert r.pop() == Book.__table__

    def test_parse_related_models_join(self):
        query = Book.query.join(Author, Book.author_id == Author.id)
        r = parse_query_related_models(query=query)
        assert len(r) == 2
        assert r == [Book.__table__, Author.__table__]

    def test_parse_related_models_subquery(self):
        subquery = Book.query.subquery(name='a')
        query = db.session.query(subquery)
        r = parse_query_related_models(query=query)
        assert len(r) == 2
        assert r == [subquery, Book.__table__]
