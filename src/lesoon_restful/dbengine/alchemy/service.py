import typing as t

from flask import current_app
from flask_sqlalchemy import get_state
from lesoon_common.dataclass.req import PageParam
from lesoon_common.globals import request as current_request
from lesoon_common.model.alchemy.base import Model
from lesoon_common.model.alchemy.schema import ModelConverter
from lesoon_common.model.alchemy.schema import SqlaModelConverter
from lesoon_common.utils.str import camelcase
from lesoon_common.wrappers import LesoonQuery
from lesoon_common.wrappers.alchemy import Pagination
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.base import class_mapper
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.sql.expression import and_
from sqlalchemy.sql.expression import or_
from sqlalchemy.sql.schema import Column

from lesoon_restful.dbengine.alchemy.filters import FILTER_NAMES
from lesoon_restful.dbengine.alchemy.filters import FILTERS_BY_FIELD
from lesoon_restful.dbengine.alchemy.utils import parse_columns
from lesoon_restful.dbengine.alchemy.utils import parse_query_related_models
from lesoon_restful.filters import BaseFilter
from lesoon_restful.filters import Condition
from lesoon_restful.filters import convert_filters
from lesoon_restful.filters import filters_for_field
from lesoon_restful.resource import ModelResource
from lesoon_restful.service import QueryService
from lesoon_restful.utils.filters import legitimize_sort
from lesoon_restful.utils.filters import legitimize_where


class SQLAlchemyService(QueryService):
    """
    SQLAlchemy服务类.
    """
    FILTER_NAMES = FILTER_NAMES
    FILTERS_BY_FIELD = FILTERS_BY_FIELD

    # model字段映射类
    model_converter: ModelConverter = SqlaModelConverter()

    def _init_model(self):
        super()._init_model()
        mapper = class_mapper(self.meta.model)

        if self.id_attribute:
            self.id_column = getattr(self.meta.model, self.id_attribute)
        else:
            self.id_column = mapper.primary_key[0]
            self.id_attribute = mapper.primary_key[0].name

    def _init_filter(self, filter_class: t.Type[BaseFilter], name: str, field,
                     attribute: str):
        if not hasattr(self.model, attribute):
            return None
        else:
            return filter_class(name,
                                field=field,
                                attribute=attribute,
                                column=getattr(self.model, attribute))

    def parse_request_by_query(self,
                               query: LesoonQuery,
                               page_param: PageParam = None,
                               request=current_request) -> PageParam:
        page_param = page_param or PageParam()
        where_dict = legitimize_where(page_param.where or request.where)
        sort_dict = legitimize_sort(page_param.sort or request.sort)

        where, sort = [], []
        models = parse_query_related_models(query=query)
        for model in models:
            where.extend(
                self._convert_filters_by_model(where=where_dict, model=model))
            sort.extend(
                list(self._convert_sort_by_model(sort=sort_dict, model=model)))

        return PageParam(page=request.page,
                         page_size=request.page_size,
                         if_page=request.if_page,
                         where=tuple(where),
                         sort=tuple(sort))

    def _convert_filters_by_model(self, where: dict,
                                  model: Model) -> t.List[Condition]:
        columns = parse_columns(data=where, model=model)
        fs = []
        for column, value in columns:
            field_cls = self.model_converter._get_field_class_for_column(  # noqa
                column)
            field_filters = filters_for_field(
                field_cls=field_cls,
                filter_names=self.FILTER_NAMES,
                filters_by_field=self.FILTERS_BY_FIELD)
            filters = {
                name: filter_cls(name, field_cls(), column.name, column)
                for name, filter_cls in field_filters.items()
            }
            fs.extend(convert_filters(value, field_filters=filters))
        return fs

    @staticmethod
    def _convert_sort_by_model(sort: t.Dict[str, bool],
                               model: Model) -> t.List[tuple]:
        columns = parse_columns(data=sort, model=model)
        return [(None, c.name, r) for c, r in columns]

    @staticmethod
    def _get_session():
        session = get_state(current_app).db.session
        if not session.is_active:
            session.begin()
        return session

    def _or_expression(self, expressions: t.List[BinaryExpression]):
        if not expressions:
            return True
        if len(expressions) == 1:
            return expressions[0]
        return or_(*expressions)

    def _and_expression(self, expressions: t.List[BinaryExpression]):
        if not expressions:
            return False
        if len(expressions) == 1:
            return expressions[0]
        return and_(*expressions)

    def _query(self) -> LesoonQuery:
        query: LesoonQuery = self.model.query
        try:
            query_options = self.meta.query_options
        except KeyError:
            return query
        return query.options(*query_options)

    def _query_filter(
        self, query: LesoonQuery, expression: t.Union[BinaryExpression,
                                                      t.List[BinaryExpression]]
    ) -> LesoonQuery:
        if not isinstance(expression, list):
            expression = [expression]
        return query.filter(*expression)

    def _query_filter_by_id(self, query: LesoonQuery, id_) -> Model:
        return query.filter(self.id_column == id_).first()

    def _query_order_by(
            self,
            query: LesoonQuery,
            sort: t.Tuple[t.Any, Column, bool] = None) -> LesoonQuery:
        order_clauses = []

        for field, attribute, reverse in sort:
            column = getattr(self.model, attribute)

            order_clauses.append(column.desc() if reverse else column.asc())

        return query.order_by(*order_clauses)

    def _query_get_first(self, query: LesoonQuery) -> Model:
        return query.first()

    def _query_get_paginated_items(self, query: LesoonQuery, page: int,
                                   page_size: int, if_page: bool) -> Pagination:
        if isinstance(query, LesoonQuery):
            return query.paginate(page=page,
                                  per_page=page_size,
                                  if_page=if_page)
        else:
            return query.paginate(page=page, per_page=page_size)

    def _query_inject_request_param(self,
                                    query: LesoonQuery,
                                    inject_where: bool = True,
                                    inject_sort: bool = True) -> LesoonQuery:
        """
        根据查询Query注入查询条件
        Args:
            query: LesoonQuery对象
            inject_where: 是否注入过滤参数
            inject_sort: 是否注入排序参数

        """
        page_param = self.parse_request_by_query(query=query)

        if inject_where and page_param.where:
            expressions = [condition() for condition in page_param.where]
            query = self._query_filter(query, self._and_expression(expressions))

        if inject_sort and page_param.sort:
            query = self._query_order_by(query, page_param.sort)
        return query

    def paginated_instances(self, page_param: PageParam = None):
        query = self._page_query()
        page_param = self.parse_request_by_query(query=query,
                                                 page_param=page_param)
        instances = self.instances(query=query,
                                   where=page_param.where,
                                   sort=page_param.sort)
        return self._query_get_paginated_items(instances,
                                               page=page_param.page,
                                               page_size=page_param.page_size,
                                               if_page=page_param.if_page)

    @property
    def session(self):
        return self._get_session()

    def set_resource_name(self, resource: t.Type[ModelResource]):
        # 未定义resource:name则默认为小写表名
        if not hasattr(resource.Meta, 'name'):
            resource.meta['name'] = camelcase(self.model.__tablename__.lower())

    def create_one(self, item: Model, commit: bool = True):
        item = super().create_one(item)
        self.commit_or_flush(commit)
        return item

    def create_many(self, items: t.List[Model], commit: bool = True):
        items = super().create_many(items)
        self.commit_or_flush(commit)
        return items

    def _create_one(self, item: Model) -> Model:
        self.session.add(item)
        self.commit_or_flush(False)
        return item

    def _create_many(self, items: t.List[Model]) -> t.List[Model]:
        self.session.bulk_save_objects(items)
        self.commit_or_flush(False)
        return items

    def update_one(self, item: Model, changes: dict, commit: bool = True):
        item = super().update_one(item, changes)
        self.commit_or_flush(commit)
        return item

    def update_many(self,
                    items: t.List[Model],
                    changes: t.List[dict],
                    commit: bool = True):
        items = super().update_many(items, changes)
        self.commit_or_flush(commit)
        return items

    def _update_one(self, item: Model, changes: dict) -> Model:
        item = self.schema.load(changes, partial=True, instance=item)  # noqa
        self.commit_or_flush(False)
        return item

    def _update_many(self, items: t.List[Model],
                     changes: t.List[dict]) -> t.List[Model]:
        updated_items = []
        for item, change in zip(items, changes):
            updated_items.append(self._update_one(item, change))

        self.commit_or_flush(False)
        return updated_items

    def delete_one(self, id_: int, commit: bool = True):
        super().delete_one(id_)
        self.commit_or_flush(commit)

    def delete_many(self, ids: t.List[int], commit: bool = True):
        super().delete_many(ids)
        self.commit_or_flush(commit)

    def _delete_one(self, id_: int):
        self._delete_many(ids=[id_])
        self.commit_or_flush(False)

    def _delete_many(self, ids: t.List[int]):
        self._query_filter(self.query, self.id_column.in_(ids)).delete()
        self.commit_or_flush(False)

    def commit(self):
        self.commit_or_flush(commit=True)

    def commit_or_flush(self, commit: bool):
        session = self.session
        try:
            if commit:
                session.commit()
            else:
                session.flush()
        except SQLAlchemyError:
            session.rollback()
            raise
