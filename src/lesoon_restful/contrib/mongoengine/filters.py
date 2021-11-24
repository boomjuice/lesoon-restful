from marshmallow import fields as ma_fields

import lesoon_restful.filters as filters


class EqualFilter(filters.EqualFilter):

    def op(self, value):
        return {self.attribute: value}


class NotEqualFilter(filters.NotEqualFilter):

    def op(self, value):
        return {f'{self.attribute}__ne': value}


class LessThanFilter(filters.LessThanFilter):

    def op(self, value):
        return {f'{self.attribute}__lt': value}


class LessThanEqualFilter(filters.LessThanEqualFilter):

    def op(self, value):
        return {f'{self.attribute}__lte': value}


class GreaterThanFilter(filters.GreaterThanFilter):

    def op(self, value):
        return {f'{self.attribute}__gt': value}


class GreaterThanEqualFilter(filters.GreaterThanEqualFilter):

    def op(self, value):
        return {f'{self.attribute}__gte': value}


class InFilter(filters.InFilter):

    def op(self, values):
        return {f'{self.attribute}__in': values}


class ContainsFilter(filters.ContainsFilter):

    def op(self, value):
        return {f'{self.attribute}__contains': value}


class StringContainsFilter(filters.StringContainsFilter):

    def op(self, value):
        return {f'{self.attribute}__contains': value}


class StringIContainsFilter(filters.StringIContainsFilter):

    def op(self, value):
        return {f'{self.attribute}__icontains': value}


class StartsWithFilter(filters.StartsWithFilter):

    def op(self, value):
        return {f'{self.attribute}__startswith': value}


class IStartsWithFilter(filters.IStartsWithFilter):

    def op(self, value):
        return {f'{self.attribute}__istartswith': value}


class EndsWithFilter(filters.EndsWithFilter):

    def op(self, value):
        return {f'{self.attribute}__endswith': value}


class IEndsWithFilter(filters.IEndsWithFilter):

    def op(self, value):
        return {f'{self.attribute}__iendswith': value}


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

FILTERS_BY_TYPE = (
    (ma_fields.Boolean, CommonFilters),
    (ma_fields.Number, CommonFilters + NumberFilters),
    (ma_fields.Float, CommonFilters + NumberFilters),
    (ma_fields.Decimal, CommonFilters + NumberFilters),
    (ma_fields.String, CommonFilters + StringFilters),
    (ma_fields.List, (ContainsFilter,)),
)
