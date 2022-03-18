import marshmallow as ma
import pytest

from lesoon_restful.exceptions import FilterNotAllow
from lesoon_restful.exceptions import InvalidParam
from lesoon_restful.filters import CommonFilters
from lesoon_restful.filters import ContainsFilter
from lesoon_restful.filters import convert_filters
from lesoon_restful.filters import EqualFilter
from lesoon_restful.filters import FILTERS_BY_FIELD
from lesoon_restful.filters import filters_for_field
from lesoon_restful.filters import filters_for_field_class
from lesoon_restful.filters import GreaterThanEqualFilter
from lesoon_restful.filters import GreaterThanFilter
from lesoon_restful.filters import InFilter
from lesoon_restful.filters import legitimize_sort
from lesoon_restful.filters import legitimize_where
from lesoon_restful.filters import LessThanEqualFilter
from lesoon_restful.filters import LessThanFilter
from lesoon_restful.filters import NotEqualFilter
from lesoon_restful.filters import NumberFilters


class TestFilters:

    def test_for_field_class(self):
        filter_cls = filters_for_field_class(ma.fields.Boolean,
                                             FILTERS_BY_FIELD)
        assert not filter_cls.difference(CommonFilters)

        filter_cls = filters_for_field_class(ma.fields.Decimal,
                                             FILTERS_BY_FIELD)
        assert not filter_cls.difference(CommonFilters + NumberFilters)

    def test_filters_for_field(self):
        field_filters = filters_for_field(ma.fields.Boolean)
        assert field_filters == {
            None: EqualFilter,
            'eq': EqualFilter,
            'ne': NotEqualFilter,
            'in': InFilter
        }
        field_filters = filters_for_field(ma.fields.Decimal)
        assert field_filters == {
            None: EqualFilter,
            'eq': EqualFilter,
            'ne': NotEqualFilter,
            'in': InFilter,
            'lt': LessThanFilter,
            'lte': LessThanEqualFilter,
            'gt': GreaterThanFilter,
            'gte': GreaterThanEqualFilter
        }

    def test_convert_filters(self):
        # test equal
        condition = convert_filters({'$eq': 1}, {
            None: EqualFilter(name='eq', field=ma.fields.Int(), attribute='id'),
            'eq': EqualFilter(name='eq', field=ma.fields.Int(), attribute='id')
        })

        assert isinstance(condition.filter, EqualFilter)
        assert condition.column == 'id'
        assert condition.value == 1

        with pytest.raises(FilterNotAllow):
            convert_filters({'$ne': 1}, {
                None:
                    EqualFilter(
                        name='eq', field=ma.fields.Int(), attribute='id'),
            })

        condition = convert_filters(
            '123', {
                None:
                    EqualFilter(
                        name='eq', field=ma.fields.Int(), attribute='id'),
                'ne':
                    NotEqualFilter(
                        name='ne', field=ma.fields.Int(), attribute='id')
            })

        assert isinstance(condition.filter, EqualFilter)
        assert condition.column == 'id'
        assert condition.value == '123'

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
