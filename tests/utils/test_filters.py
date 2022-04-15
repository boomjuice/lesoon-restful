import typing as t

import pytest

from lesoon_restful import filters
from lesoon_restful.utils.filters import legitimize_sort
from lesoon_restful.utils.filters import legitimize_where
from lesoon_restful.utils.filters import Where as _Where


class Where(_Where):

    def convert2param(self, op: str, name: str, value: t.Any):
        self._data[name] = f'{op}-{value}'


class TestFilters:

    def test_legitimize_where(self):
        where = {'a': 1}
        assert legitimize_where(where) == {'a': 1}

        where = {'a_eq': 1}
        assert legitimize_where(where) == {'a': {'$eq': 1}}

        where = {'a_in': [1, 2, 3]}
        assert legitimize_where(where) == {'a': {'$in': [1, 2, 3]}}

    def test_legitimize_sort(self):
        sort = 'a'
        assert legitimize_sort(sort) == {'a': False}

        sort = 'a asc'
        assert legitimize_sort(sort) == {'a': False}

        sort = 'a asc,b desc'
        assert legitimize_sort(sort) == {'a': False, 'b': True}

        sort = {'a': False}
        assert legitimize_sort(sort) == sort


class TestWhere:

    def test_eq(self):
        where = Where()
        where.equal('a', 1)
        assert 'a' in where._data
        assert where._data['a'] == f'{filters.Equal}-1'

    def test_neq(self):
        where = Where()
        where.not_equal('a', 1)
        assert 'a' in where._data
        assert where._data['a'] == f'{filters.NotEqual}-1'

    def test_lt(self):
        where = Where()
        where.less_than('a', 1)
        assert 'a' in where._data
        assert where._data['a'] == f'{filters.LessThan}-1'

    def test_lte(self):
        where = Where()
        where.less_than_equal('a', 1)
        assert 'a' in where._data
        assert where._data['a'] == f'{filters.LessThanEqual}-1'

    def test_gt(self):
        where = Where()
        where.greater_than('a', 1)
        assert 'a' in where._data
        assert where._data['a'] == f'{filters.GreaterThan}-1'

    def test_gte(self):
        where = Where()
        where.greater_than_equal('a', 1)
        assert 'a' in where._data
        assert where._data['a'] == f'{filters.GreaterThanEqual}-1'

    def test_in(self):
        where = Where()
        where.in_('a', [1, 2])
        assert 'a' in where._data
        assert where._data['a'] == f'{filters.In}-[1, 2]'

    def test_nin(self):
        where = Where()
        where.not_in('a', [1, 2])
        assert 'a' in where._data
        assert where._data['a'] == f'{filters.NotIn}-[1, 2]'

    def test_contains(self):
        where = Where()
        where.contains('a', 1)
        assert 'a' in where._data
        assert where._data['a'] == f'{filters.Contains}-1'

    def test_startswith(self):
        where = Where()
        where.startswith('a', 1)
        assert 'a' in where._data
        assert where._data['a'] == f'{filters.StartsWith}-1'

    def test_endswith(self):
        where = Where()
        where.endswith('a', 1)
        assert 'a' in where._data
        assert where._data['a'] == f'{filters.EndsWith}-1'
