""" 通用Schema基类模块. """
import sqlalchemy as sa
from flask import Request
from flask_sqlalchemy import Model
from lesoon_common.extensions import db
from lesoon_common.model import fields
from lesoon_common.utils.str import camelcase
from marshmallow import EXCLUDE
from marshmallow import Schema
from marshmallow_sqlalchemy import ModelConverter
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow_sqlalchemy import SQLAlchemySchema
from sqlalchemy.dialects import mysql
from sqlalchemy.sql import sqltypes


class CustomModelConverter(ModelConverter):
    SQLA_TYPE_MAPPING = {
        sa.Enum: fields.Field,
        sa.JSON: fields.Raw,
        mysql.BIT: fields.Integer,
        mysql.YEAR: fields.Integer,
        mysql.SET: fields.List,
        mysql.ENUM: fields.Field,
        mysql.INTEGER: fields.Integer,
        mysql.DATETIME: fields.DateTime,
        mysql.BIGINT: fields.IntStr,
        sqltypes.BigInteger: fields.IntStr,
    }


class FixedOperatorSchema:
    # 不准前端更新字段
    creator = fields.Str(dump_only=True)
    modifier = fields.Str(dump_only=True)
    create_time = fields.DateTime(dump_only=True)
    modify_time = fields.DateTime(dump_only=True)
    update_time = fields.DateTime(dump_only=True)


class SqlaCamelSchema(SQLAlchemySchema, FixedOperatorSchema):
    # id字段只准序列化,不准反序列读取以防更新数据库id
    id = fields.IntStr(dump_only=True)

    class Meta:
        # 如果load的键没有匹配到定义的field时的操作,
        # RAISE: 如果存在未知key,引发ValidationError
        # EXCLUDE: 忽略未知key
        # INCLUDE: 包含未知可以,即使时未定义的field
        unknown: str = EXCLUDE
        # 排除字段
        exclude: list = []
        # 保持有序
        ordered = True
        # 时间格式
        datetimeformat = '%Y-%m-%d %H:%M:%S'
        # sqlalchemy-model
        model: Model = None
        # sqlalchemy-session
        sqla_session = db.session
        # 是否能通过实例对象序列化
        load_instance: bool = True
        # 是否包含Model的关联关系
        include_relationships: bool = False
        # model字段映射类
        model_converter: ModelConverter = CustomModelConverter


class SqlaCamelAutoSchema(SqlaCamelSchema, SQLAlchemyAutoSchema):
    pass
