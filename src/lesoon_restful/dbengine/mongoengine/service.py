import typing as t

from flask_mongoengine import BaseQuerySet
from flask_mongoengine import Document
from lesoon_common.utils.str import camelcase

from lesoon_restful.dbengine.mongoengine.filters import FILTER_NAMES
from lesoon_restful.dbengine.mongoengine.filters import FILTERS_BY_FIELD
from lesoon_restful.resource import ModelResource
from lesoon_restful.service import QueryService


class MongoEngineService(QueryService):
    """
    A service for MongoEngine documents.

    """
    FILTER_NAMES = FILTER_NAMES
    FILTERS_BY_FIELD = FILTERS_BY_FIELD

    def _init_model(self):
        super()._init_model()
        self.id_column = self.model._fields[self.id_attribute]  # noqa

    def _and_expression(self, expressions: t.List[dict]):
        and_expression: t.Dict[str, str] = {}
        for expression in expressions:
            and_expression.update(**expression)
        return and_expression

    def _or_expression(self, expressions):
        # TODO:暂未实现
        pass

    def _query(self):
        return self.model.objects

    def _query_filter(self, query: BaseQuerySet, expression: dict):
        return query(**expression)

    def _query_get_first(self, query: BaseQuerySet):
        return query.first()

    def _query_filter_by_id(self, query: BaseQuerySet, id_: t.Any):
        return query(**{self.id_attribute: id_}).first()

    def _query_order_by(self, query: BaseQuerySet, sort: t.Tuple = None):
        order_clauses = []

        for field, attribute, reverse in sort:
            if reverse:
                order_clauses.append(f'-{attribute}')
            else:
                order_clauses.append(f'+{attribute}')
        return query.order_by(*order_clauses)

    def _query_get_paginated_items(self, query: BaseQuerySet, page: int,
                                   page_size: int, if_page: bool):
        return query.paginate(page=page, per_page=page_size, if_page=if_page)

    def set_resource_name(self, resource: t.Type[ModelResource]):
        # 没有资源名称,则取模型对应的集合名称
        if not hasattr(resource.Meta, 'name'):
            name = self.model._meta.get('collection',
                                        self.model.__class__.__name__).lower()
            resource.meta['name'] = camelcase(name)

    def _create_one(self, item: Document):
        item.save()
        return item

    def _create_many(self, items: t.List[Document]):
        self.query.insert(items)
        return items

    def _update_one(self, item: Document, changes: dict):
        item = self.schema.load(changes, instance=item, partial=True)  # noqa
        item.save()
        return item

    def _update_many(self, items: t.List[Document],
                     changes: t.List[dict]) -> t.List[Document]:
        updated_items = []
        for item, change in zip(items, changes):
            updated_items.append(self._update_one(item, change))

        return updated_items

    def _delete_one(self, id_: int):
        self._delete_many(ids=[id_])

    def _delete_many(self, ids: t.List[int]):
        self._query_filter(self.query, {
            f'{self.id_attribute}__in': ids
        }).delete()
