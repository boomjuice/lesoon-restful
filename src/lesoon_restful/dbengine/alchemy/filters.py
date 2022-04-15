import typing as t

from lesoon_common.utils.str import camelcase
from marshmallow import fields as ma_fields

from lesoon_restful import filters
from lesoon_restful.utils.filters import Where as _Where

EqualFilter = filters.EqualFilter
NotEqualFilter = filters.NotEqualFilter
LessThanFilter = filters.LessThanFilter
LessThanEqualFilter = filters.LessThanEqualFilter
GreaterThanFilter = filters.GreaterThanFilter
GreaterThanEqualFilter = filters.GreaterThanEqualFilter

# ShortName
NotIn = 'notIn'
Like = 'like'
Ilike = 'ilike'
PrefixLike = 'prefixLike'
SuffixLike = 'suffixLike'


class BaseFilter(filters.BaseFilter):
    DELIMITED_FILTER_NAMES = (filters.In, NotIn)


class InFilter(BaseFilter):

    def op(self, column, value):
        if isinstance(value, str):
            value = value.split(',')
        return column.in_(value) if len(value) else False


class NotInFilter(BaseFilter):

    def op(self, column, value):
        if isinstance(value, str):
            value = value.split(',')
        return column.notin_(value) if len(value) else False


class ContainsFilter(BaseFilter):

    def op(self, column, value):
        return column.contains(value)


class StringContainsFilter(BaseFilter):

    def op(self, column, value):
        return column.like('%' + value.replace('%', '\\%') + '%')


class StringIContainsFilter(BaseFilter):

    def op(self, column, value):
        return column.ilike('%' + value.replace('%', '\\%') + '%')


class StartsWithFilter(BaseFilter):

    def op(self, column, value):
        return column.startswith(value.replace('%', '\\%'))


class IStartsWithFilter(BaseFilter):

    def op(self, column, value):
        return column.ilike(value.replace('%', '\\%') + '%')


class EndsWithFilter(BaseFilter):

    def op(self, column, value):
        return column.endswith(value.replace('%', '\\%'))


class IEndsWithFilter(BaseFilter):

    def op(self, column, value):
        return column.ilike('%' + value.replace('%', '\\%'))


class DateBetweenFilter(BaseFilter):

    def op(self, column, value):
        return column.between(value[0], value[1])


CommonFilters = (EqualFilter, NotEqualFilter, InFilter, NotInFilter)
NumberFilters = (LessThanFilter, LessThanEqualFilter, GreaterThanFilter,
                 GreaterThanEqualFilter)
StringFilters = (StringContainsFilter, StringIContainsFilter, StartsWithFilter,
                 IStartsWithFilter, EndsWithFilter, IEndsWithFilter)
DateTypeFilters = (DateBetweenFilter,)

FILTER_NAMES = (
    (EqualFilter, None),
    (EqualFilter, filters.Equal),
    (NotEqualFilter, filters.NotEqual),
    (LessThanFilter, filters.LessThan),
    (LessThanEqualFilter, filters.LessThanEqual),
    (GreaterThanFilter, filters.GreaterThan),
    (GreaterThanEqualFilter, filters.GreaterThanEqual),
    (InFilter, filters.In),
    (ContainsFilter, filters.Contains),
    (StringContainsFilter, filters.Contains),
    (StringIContainsFilter, filters.IContains),
    (StartsWithFilter, filters.StartsWith),
    (IStartsWithFilter, filters.IStartsWith),
    (EndsWithFilter, filters.EndsWith),
    (IEndsWithFilter, filters.IEndsWith),
    (DateBetweenFilter, filters.Between),
    # TODO: JAVA体系定义
    (NotInFilter, NotIn),
    (ContainsFilter, Like),
    (StringContainsFilter, Like),
    (StringIContainsFilter, Ilike),
    (StartsWithFilter, PrefixLike),
    (EndsWithFilter, SuffixLike),
)

FILTERS_BY_FIELD = (
    (ma_fields.Boolean, CommonFilters),
    (ma_fields.Number, CommonFilters + NumberFilters),
    (ma_fields.Float, CommonFilters + NumberFilters),
    (ma_fields.Decimal, CommonFilters + NumberFilters),
    (ma_fields.String, CommonFilters + StringFilters),
    (ma_fields.Date, CommonFilters + NumberFilters + DateTypeFilters),
    (ma_fields.DateTime, CommonFilters + NumberFilters + DateTypeFilters),
    (ma_fields.List, (ContainsFilter,)),
)


class Where(_Where):

    def convert2param(self, op: str, name: str, value: t.Any):
        self._data[f'{camelcase(name)}_{op}'] = value

    def in_(self, name: str, value: list):
        return self.convert2param(filters.In, name, ','.join(map(str, value)))

    def not_in(self, name: str, value: list):
        return self.convert2param(NotIn, name, ','.join(map(str, value)))

    def contains(self, name: str, value: t.Any):
        return self.convert2param(Like, name, value)

    def startswith(self, name: str, value: t.Any):
        return self.convert2param(PrefixLike, name, value)

    def endswith(self, name: str, value: t.Any):
        return self.convert2param(SuffixLike, name, value)
