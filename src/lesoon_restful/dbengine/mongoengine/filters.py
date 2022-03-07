from marshmallow import fields as ma_fields

from lesoon_restful import filters


class EqualFilter(filters.EqualFilter):

    def op(self, column, value):
        return {column: value}


class NotEqualFilter(filters.NotEqualFilter):

    def op(self, column, value):
        return {f'{column}__ne': value}


class LessThanFilter(filters.LessThanFilter):

    def op(self, column, value):
        return {f'{column}__lt': value}


class LessThanEqualFilter(filters.LessThanEqualFilter):

    def op(self, column, value):
        return {f'{column}__lte': value}


class GreaterThanFilter(filters.GreaterThanFilter):

    def op(self, column, value):
        return {f'{column}__gt': value}


class GreaterThanEqualFilter(filters.GreaterThanEqualFilter):

    def op(self, column, value):
        return {f'{column}__gte': value}


class InFilter(filters.InFilter):

    def op(self, column, value):
        return {f'{column}__in': value}


class ContainsFilter(filters.ContainsFilter):

    def op(self, column, value):
        return {f'{column}__contains': value}


class StringContainsFilter(filters.StringContainsFilter):

    def op(self, column, value):
        return {f'{column}__contains': value}


class StringIContainsFilter(filters.StringIContainsFilter):

    def op(self, column, value):
        return {f'{column}__icontains': value}


class StartsWithFilter(filters.StartsWithFilter):

    def op(self, column, value):
        return {f'{column}__startswith': value}


class IStartsWithFilter(filters.IStartsWithFilter):

    def op(self, column, value):
        return {f'{column}__istartswith': value}


class EndsWithFilter(filters.EndsWithFilter):

    def op(self, column, value):
        return {f'{column}__endswith': value}


class IEndsWithFilter(filters.IEndsWithFilter):

    def op(self, column, value):
        return {f'{column}__iendswith': value}


CommonFilters = (EqualFilter, NotEqualFilter, InFilter)
NumberFilters = (LessThanFilter, LessThanEqualFilter, GreaterThanFilter,
                 GreaterThanEqualFilter)
StringFilters = (StringContainsFilter, StringIContainsFilter, StartsWithFilter,
                 IStartsWithFilter, EndsWithFilter, IEndsWithFilter)

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
)

FILTERS_BY_FIELD = (
    (ma_fields.Boolean, CommonFilters),
    (ma_fields.Number, CommonFilters + NumberFilters),
    (ma_fields.Float, CommonFilters + NumberFilters),
    (ma_fields.Decimal, CommonFilters + NumberFilters),
    (ma_fields.String, CommonFilters + StringFilters),
    (ma_fields.List, ContainsFilter),
)
