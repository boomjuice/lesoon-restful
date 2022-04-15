import marshmallow as ma
import pytest

from lesoon_restful import filters
from lesoon_restful.exceptions import FilterNotAllow
from lesoon_restful.filters import CommonFilters
from lesoon_restful.filters import convert_filters
from lesoon_restful.filters import EqualFilter
from lesoon_restful.filters import FILTERS_BY_FIELD
from lesoon_restful.filters import filters_for_field
from lesoon_restful.filters import filters_for_field_class
from lesoon_restful.filters import GreaterThanEqualFilter
from lesoon_restful.filters import GreaterThanFilter
from lesoon_restful.filters import InFilter
from lesoon_restful.filters import LessThanEqualFilter
from lesoon_restful.filters import LessThanFilter
from lesoon_restful.filters import NotEqualFilter
from lesoon_restful.filters import NotInFilter
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
            filters.Equal: EqualFilter,
            filters.NotEqual: NotEqualFilter,
            filters.In: InFilter,
            filters.NotIn: NotInFilter
        }
        field_filters = filters_for_field(ma.fields.Decimal)
        assert field_filters == {
            None: EqualFilter,
            filters.Equal: EqualFilter,
            filters.NotEqual: NotEqualFilter,
            filters.In: InFilter,
            filters.NotIn: NotInFilter,
            filters.LessThan: LessThanFilter,
            filters.LessThanEqual: LessThanEqualFilter,
            filters.GreaterThan: GreaterThanFilter,
            filters.GreaterThanEqual: GreaterThanEqualFilter
        }

    def test_convert_filters(self):
        # test equal
        condition = convert_filters({'$eq': 1}, {
            None: EqualFilter(name='eq', field=ma.fields.Int(), attribute='id'),
            'eq': EqualFilter(name='eq', field=ma.fields.Int(), attribute='id')
        })

        assert len(condition) == 1
        c = condition[0]
        assert isinstance(c.filter, EqualFilter)
        assert c.column == 'id'
        assert c.value == 1

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

        assert len(condition) == 1
        c = condition[0]
        assert isinstance(c.filter, EqualFilter)
        assert c.column == 'id'
        assert c.value == 123

        # more filters
        condition = convert_filters({
            '$lte': 1,
            '$gte': 2
        }, {
            None:
                EqualFilter(name='eq', field=ma.fields.Int(), attribute='id'),
            'gte':
                GreaterThanEqualFilter(
                    name='gte', field=ma.fields.Int(), attribute='id'),
            'lte':
                LessThanEqualFilter(
                    name='lte', field=ma.fields.Int(), attribute='id')
        })

        assert len(condition) == 2
        c = condition[0]
        assert isinstance(c.filter, LessThanEqualFilter)
        assert c.column == 'id'
        assert c.value == 1

        c = condition[1]
        assert isinstance(c.filter, GreaterThanEqualFilter)
        assert c.column == 'id'
        assert c.value == 2
