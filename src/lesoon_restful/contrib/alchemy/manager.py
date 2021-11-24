import typing as t

from flask import current_app
from flask_sqlalchemy import get_state
from sqlalchemy import and_
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import class_mapper

from lesoon_restful.contrib.alchemy.filters import FILTER_NAMES
from lesoon_restful.contrib.alchemy.filters import FILTERS_BY_TYPE
from lesoon_restful.manager import QueryManager
from lesoon_restful.resource import ModelResource
from lesoon_restful.signals import after_create
from lesoon_restful.signals import after_delete
from lesoon_restful.signals import after_update
from lesoon_restful.signals import before_create
from lesoon_restful.signals import before_delete
from lesoon_restful.signals import before_update


class SQLAlchemyManager(QueryManager):
    """
    A manager for SQLAlchemy models.


    """
    FILTER_NAMES = FILTER_NAMES
    FILTERS_BY_TYPE = FILTERS_BY_TYPE

    def _init_model(self, resource: t.Type[ModelResource], model, meta):
        super()._init_model(resource, model, meta)
        mapper = class_mapper(model)

        if self.id_attribute:
            self.id_column = getattr(model, self.id_attribute)
        else:
            self.id_column = mapper.primary_key[0]
            self.id_attribute = mapper.primary_key[0].name

        # 未定义resource:name则默认为小写表名
        if not hasattr(resource.Meta, 'name'):
            meta['name'] = model.__tablename__.lower()

    def _init_filter(self, filter_class, name: str, field, attribute: str):
        return filter_class(name,
                            field=field,
                            attribute=attribute,
                            column=getattr(self.model, attribute))

    @staticmethod
    def _get_session():
        return get_state(current_app).db.session

    def _or_expression(self, expressions):
        if not expressions:
            return True
        if len(expressions) == 1:
            return expressions[0]
        return or_(*expressions)

    def _and_expression(self, expressions):
        if not expressions:
            return False
        if len(expressions) == 1:
            return expressions[0]
        return and_(*expressions)

    def _query(self):
        query = self.model.query
        try:
            query_options = self.resource.meta.query_options
        except KeyError:
            return query
        return query.options(*query_options)

    def _query_filter(self, query, expression):
        return query.filter(expression)

    def _query_get_first(self, query):
        return query.first()

    def _query_filter_by_id(self, query, id):
        return query.filter(self.id_column == id).first()

    def _query_order_by(self, query, sort=None):
        order_clauses = []

        for field, attribute, reverse in sort:
            column = getattr(self.model, attribute)

            order_clauses.append(column.desc() if reverse else column.asc())

        return query.order_by(*order_clauses)

    def _query_get_paginated_items(self, query, page, per_page):
        return query.paginate(page=page, per_page=per_page)

    def create(self, properties, commit=True):
        item = self.resource.schema.load(properties)
        before_create.send(self.resource, item=item)

        session = self._get_session()
        session.add(item)
        self.commit_or_flush(commit)

        after_create.send(self.resource, item=item)

        return item

    def update(self, item, changes, commit=True):
        before_update.send(self.resource, item=item, changes=changes)

        item = self.resource.schema.load(changes, instance=item)
        self.commit_or_flush(commit)

        after_update.send(self.resource, item=item, changes=changes)
        return item

    def delete(self, item, commit=True):
        session = self._get_session()

        before_delete.send(self.resource, item=item)

        session.delete(item)
        self.commit_or_flush(commit)

        after_delete.send(self.resource, item=item)

    def commit(self):
        session = self._get_session()
        session.commit()

    def commit_or_flush(self, commit):
        session = self._get_session()
        try:
            if commit:
                session.commit()
            else:
                session.flush()
        except SQLAlchemyError:
            session.rollback()
            raise
