import typing as t

from flask_mongoengine import BaseQuerySet

from lesoon_restful.contrib.mongoengine.filters import FILTER_NAMES
from lesoon_restful.contrib.mongoengine.filters import FILTERS_BY_TYPE
from lesoon_restful.manager import QueryManager
from lesoon_restful.signals import after_create
from lesoon_restful.signals import after_delete
from lesoon_restful.signals import after_update
from lesoon_restful.signals import before_create
from lesoon_restful.signals import before_delete
from lesoon_restful.signals import before_update


class MongoEngineManager(QueryManager):
    """
    A manager for MongoEngine documents.

    """
    FILTER_NAMES = FILTER_NAMES
    FILTERS_BY_TYPE = FILTERS_BY_TYPE

    def __init__(self, resource, model):
        super().__init__(resource, model)

    def _init_model(self, resource, model, meta):
        super()._init_model(resource, model, meta)
        self.id_column = model._fields[self.id_attribute]

        # resource name: use model collection's name if not set explicitly
        if not hasattr(resource.Meta, 'name'):
            meta['name'] = model._meta.get('collection',
                                           model.__class__.__name__).lower()

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

    def _query_get_first(self, query):
        return query.first()

    def _query_filter_by_id(self, query: BaseQuerySet, id: t.Any):
        return query(**{self.id_attribute: id}).first()

    def _query_order_by(self, query: BaseQuerySet, sort: t.Tuple = None):
        order_clauses = []

        for field, attribute, reverse in sort:
            if reverse:
                order_clauses.append(f'-{attribute}')
            else:
                order_clauses.append(f'+{attribute}')
        return query.order_by(*order_clauses)

    def _query_get_paginated_items(self, query: BaseQuerySet, page: int,
                                   per_page: int):
        return query.paginate(page=page, per_page=per_page)

    def create(self, properties: dict, commit=True):
        item = self.resource.schema.load(properties)

        before_create.send(self.resource, item=item)

        item.save()
        after_create.send(self.resource, item=item)

        return item

    def update(self, item, changes, commit=True):
        before_update.send(self.resource, item=item, changes=changes)

        item = self.resource.schema.load(changes, instance=item)  # noqa
        item.save()

        after_update.send(self.resource, item=item, changes=changes)
        return item

    def delete(self, item):
        before_delete.send(self.resource, item=item)
        item.delete()
        after_delete.send(self.resource, item=item)
