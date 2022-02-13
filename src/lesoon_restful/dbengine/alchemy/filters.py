from marshmallow import fields as ma_fields

from lesoon_restful import filters

EqualFilter = filters.EqualFilter
NotEqualFilter = filters.NotEqualFilter
LessThanFilter = filters.LessThanFilter
LessThanEqualFilter = filters.LessThanEqualFilter
GreaterThanFilter = filters.GreaterThanFilter
GreaterThanEqualFilter = filters.GreaterThanEqualFilter


class InFilter(filters.InFilter):

    def op(self, column, value):
        return column.in_(value) if len(value) else False


class ContainsFilter(filters.ContainsFilter):

    def op(self, column, value):
        return column.contains(value)


class StringContainsFilter(filters.StringContainsFilter):

    def op(self, column, value):
        return column.like('%' + value.replace('%', '\\%') + '%')


class StringIContainsFilter(filters.StringIContainsFilter):

    def op(self, column, value):
        return column.ilike('%' + value.replace('%', '\\%') + '%')


class StartsWithFilter(filters.StartsWithFilter):

    def op(self, column, value):
        return column.startswith(value.replace('%', '\\%'))


class IStartsWithFilter(filters.IStartsWithFilter):

    def op(self, column, value):
        return column.ilike(value.replace('%', '\\%') + '%')


class EndsWithFilter(filters.EndsWithFilter):

    def op(self, column, value):
        return column.endswith(value.replace('%', '\\%'))


class IEndsWithFilter(filters.IEndsWithFilter):

    def op(self, column, value):
        return column.ilike('%' + value.replace('%', '\\%'))


class DateBetweenFilter(filters.DateBetweenFilter):

    def op(self, column, value):
        return column.between(value[0], value[1])


CommonFilters = (EqualFilter, NotEqualFilter, InFilter)
NumberFilters = (LessThanFilter, LessThanEqualFilter, GreaterThanFilter,
                 GreaterThanEqualFilter)
StringFilters = (StringContainsFilter, StringIContainsFilter, StartsWithFilter,
                 IStartsWithFilter, EndsWithFilter, IEndsWithFilter)
DateTypeFilters = (DateBetweenFilter,)

FILTER_NAMES = (
    (EqualFilter, None),
    (EqualFilter, 'eq'),
    (NotEqualFilter, 'ne'),
    (LessThanFilter, 'lt'),
    (LessThanEqualFilter, 'lte'),
    (GreaterThanFilter, 'gt'),
    (GreaterThanEqualFilter, 'gte'),
    (InFilter, 'in'),
    (ContainsFilter, 'contains'),
    (StringContainsFilter, 'contains'),
    (StringIContainsFilter, 'icontains'),
    (StartsWithFilter, 'startswith'),
    (IStartsWithFilter, 'istartswith'),
    (EndsWithFilter, 'endswith'),
    (IEndsWithFilter, 'iendswith'),
    (DateBetweenFilter, 'between'),
)

FILTERS_BY_FIELD = (
    (ma_fields.Boolean, CommonFilters),
    (ma_fields.Number, CommonFilters + NumberFilters),
    (ma_fields.Float, CommonFilters + NumberFilters),
    (ma_fields.Decimal, CommonFilters + NumberFilters),
    (ma_fields.String, CommonFilters + StringFilters),
    (ma_fields.Date, CommonFilters + NumberFilters + DateTypeFilters),
    (ma_fields.DateTime, CommonFilters + NumberFilters + DateTypeFilters),
    (ma_fields.List, ContainsFilter),
)
