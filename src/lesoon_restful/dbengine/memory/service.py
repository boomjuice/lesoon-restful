import typing as t

from lesoon_common.dataclass.req import PageParam
from marshmallow.utils import get_value

from lesoon_restful.exceptions import ItemNotFound
from lesoon_restful.filters import BaseFilter
from lesoon_restful.service import QueryService


class Pagination:

    def __init__(self, items, page, per_page, total):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total

    @classmethod
    def from_list(cls, items, page, per_page, if_page):
        if if_page:
            start = per_page * (page - 1)
            items = items[start:start + per_page]
        else:
            items = items
        return Pagination(items, page, per_page, len(items))


class MemoryService(QueryService):  # noqa
    """
    内存服务类.
    注意:
        此服务类只用于debug以及单元测试.
    """

    def __init__(self, meta=None, resource=None):
        super().__init__(meta, resource)
        self.id_sequence = 0
        self.items = {}

    def _new_item_id(self):
        self.id_sequence += 1
        return self.id_sequence

    @staticmethod
    def _filter_items(items, conditions):
        for item in items:
            if all(
                    condition(get_value(item, condition.column))
                    for condition in conditions):
                yield item

    @staticmethod
    def _sort_items(items, sort):
        for field, key, reverse in reversed(sort):
            items = sorted(items,
                           key=lambda item: get_value(key, item, None),
                           reverse=reverse)
        return items

    def _query_get_paginated_items(self, items, page, page_size, if_page):
        return Pagination.from_list(items, page, page_size, if_page)

    def instances(self, query=None, where=None, sort=None):
        items = self.items.values()

        if where is not None:
            items = list(self._filter_items(items, where))
        if sort is not None:
            items = self._sort_items(items, sort)

        return items

    def first(self, where=None, sort=None):
        try:
            return next(self.instances(where, sort))
        except StopIteration:
            raise ItemNotFound()

    def _create_one(self, item: dict):
        item_id = self._new_item_id()
        if not self.id_attribute in item:
            item[self.id_attribute] = item_id
        else:
            self.id_sequence = item[self.id_attribute]
        self.items[item_id] = item
        return item

    def _create_many(self, items: t.List[dict]):
        new_items = []
        for item in items:
            new_items.append(self._create_one(item=item))
        return new_items

    def _update_one(self, item: dict, changes: dict):
        item.update(changes)
        item_id = item[self.id_attribute]

        self.items[item_id] = item
        return item

    def _update_many(self, items: t.List[dict], changes: t.List[dict]):
        updated_items = []
        for item, change in zip(items, changes):
            updated_items.append(self._update_one(item, changes=change))

        return updated_items

    def _delete_one(self, id_: int):
        del self.items[id_]

    def _delete_many(self, ids: t.List[int]):
        for id_ in ids:
            self._delete_one(id_)

    def read(self, id_):
        return self.items.get(id_)
