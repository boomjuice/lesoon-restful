import collections.abc
import re
import typing as t

from lesoon_restful import exceptions
from lesoon_restful import filters


def legitimize_where(where: t.Dict[str, t.Any]):
    """
    将查询参数转换成标准过滤条件.
    Args:
        where: {'a_eq':1}
        where: {'a_gte':1 ,'a_lte':2}
    Returns:
        new_where: {'a':{'$eq': 1}}
        new_where: {'a':{'$gte':1 , '$lte': 2}}
    """
    new_where: t.Dict[str, t.Any] = collections.defaultdict(dict)
    for name, value in list(where.items()):
        if '_' in name:
            column, condition = name.split('_', 1)
            new_where[column][f'${condition}'] = value
        else:
            new_where[name] = value
    return new_where


def legitimize_sort(sort: t.Union[str, dict]) -> t.Dict[str, bool]:
    """
       将排序条件标准化.
       Args:
           sort: "a asc,b desc"

       Returns:
           new_sort: {'a':False,'b': True}
    """
    if isinstance(sort, str):
        if ' ' not in sort:
            return {sort: False}
        if re.match(r'[,\w]+ ((asc)|(desc))', sort):
            new_sort = {}
            for s in sort.split(','):
                # s = 'id asc' or 'id desc'
                col, order = s.split(' ', 1)
                new_sort[col] = False if order == 'asc' else True
            return new_sort
        else:
            raise exceptions.InvalidParam(msg=f'排序参数不合法:{sort}')
    return sort


class Where(collections.abc.Mapping):

    def __init__(self):
        self._data = {}

    def __getitem__(self, key):
        return self._data.__getitem__(key)

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def convert2param(self, op: str, name: str, value: t.Any):
        raise NotImplementedError

    def equal(self, name: str, value: t.Any):
        return self.convert2param(filters.Equal, name, value)

    def not_equal(self, name: str, value: t.Any):
        return self.convert2param(filters.NotEqual, name, value)

    def less_than(self, name: str, value: t.Any):
        return self.convert2param(filters.LessThan, name, value)

    def less_than_equal(self, name: str, value: t.Any):
        return self.convert2param(filters.LessThanEqual, name, value)

    def greater_than(self, name: str, value: t.Any):
        return self.convert2param(filters.GreaterThan, name, value)

    def greater_than_equal(self, name: str, value: t.Any):
        return self.convert2param(filters.GreaterThanEqual, name, value)

    def in_(self, name: str, value: list):
        return self.convert2param(filters.In, name, value)

    def not_in(self, name: str, value: list):
        return self.convert2param(filters.NotIn, name, value)

    def contains(self, name: str, value: t.Any):
        return self.convert2param(filters.Contains, name, value)

    def startswith(self, name: str, value: t.Any):
        return self.convert2param(filters.StartsWith, name, value)

    def endswith(self, name: str, value: t.Any):
        return self.convert2param(filters.EndsWith, name, value)
