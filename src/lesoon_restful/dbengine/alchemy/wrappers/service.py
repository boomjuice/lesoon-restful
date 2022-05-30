import typing
import typing as t

from lesoon_common.exceptions import ServiceError
from lesoon_common.globals import request as current_request
from lesoon_common.model.alchemy.base import Model
from lesoon_common.response import error_response
from lesoon_common.response import success_response
from lesoon_common.utils.str import udlcase
from lesoon_common.wrappers import LesoonQuery

from lesoon_restful.dbengine.alchemy.service import SQLAlchemyService
from lesoon_restful.dbengine.alchemy.utils import parse_valid_model_attribute
from lesoon_restful.dbengine.alchemy.wrappers.dataclass import ImportParam
from lesoon_restful.dbengine.alchemy.wrappers.dataclass import ImportParseResult
from lesoon_restful.dbengine.alchemy.wrappers.utils import parse_import_data


class UnionServiceMixin:

    @t.no_type_check
    def union_operate(self,
                      insert_rows: t.List[dict],
                      update_rows: t.List[dict],
                      delete_rows: t.List[int],
                      commit: bool = True):
        """新增，更新，删除的联合操作."""
        if insert_rows:
            self.create_many(items=self.schema.load(insert_rows, many=True),
                             commit=False)
        if update_rows:
            self.update_many(items=[
                self.read_or_raise(r.get(self.id_attribute))
                for r in update_rows
            ],
                             changes=update_rows,
                             commit=False)
        if delete_rows:
            self.delete_many(ids=delete_rows, commit=False)

        if insert_rows or update_rows or delete_rows:
            self.commit_or_flush(commit)


class ComplexServiceMixin:

    def before_import_data(self, param: 'ImportParam'):
        """ 导入数据前置操作. """
        pass

    @t.no_type_check
    def before_import_insert_one(self, obj: 'Model', param: 'ImportParam'):
        """
        导入数据写库前操作.
        默认会进行查库校验当前对象是否存在
        """
        union_filter = list()
        for key in param.union_key:
            attr = parse_valid_model_attribute(key, self.model)
            union_filter.append(attr.__eq__(getattr(obj, udlcase(key))))

        if len(union_filter) and obj.query.filter(*union_filter).count():
            msg_detail = (f'Excel [{obj.excel_row_pos}行,] '
                          f'根据约束[{param.union_key_name}]数据已存在')
            if param.validate_all:
                obj.error = msg_detail
            else:
                raise ServiceError(msg=msg_detail)

    def after_import_data(self, param: 'ImportParam'):
        """ 导入数据后置操作. """
        pass

    @t.no_type_check
    def process_import_data(self, param: ImportParam,
                            parsed_result: ImportParseResult):
        """导入操作写库逻辑."""
        objs = list()
        for obj in parsed_result.obj_list:
            self.before_import_insert_one(obj=obj, param=param)
            if hasattr(obj, 'error'):
                parsed_result.insert_err_list.append(obj.error)
            else:
                objs.append(obj)

        self.create_many(objs, commit=False)
        parsed_result.obj_list = objs
        self.commit()

    @t.no_type_check
    def import_data(self, param: ImportParam):
        """数据导入入口."""
        self.before_import_data(param=param)

        parsed_result: ImportParseResult = parse_import_data(param, self.model)

        if parsed_result.parse_err_list:
            msg_detail = '数据异常<br/>' + '<br/>'.join(
                parsed_result.parse_err_list)
            return error_response(msg=f'导入异常,请根据错误信息检查数据\n {msg_detail}',
                                  msg_detail=msg_detail)

        if not parsed_result.obj_list:
            msg_detail = '<br/>'.join(parsed_result.insert_err_list)
            return error_response(msg='未解析到数据', msg_detail=msg_detail)

        self.process_import_data(param, parsed_result)

        self.after_import_data(param=param)

        if parsed_result.insert_err_list:
            msg_detail = ' \n '.join(parsed_result.insert_err_list)
            return error_response(
                msg=f'导入结果: '
                f'成功条数[{len(parsed_result.obj_list)}] '
                f'失败条数[{len(parsed_result.insert_err_list)}] \n'
                f'失败信息：{msg_detail}',
                msg_detail=f'失败信息:{msg_detail}',
            )
        else:
            return success_response(
                msg=f'导入成功: 成功条数[{len(parsed_result.obj_list)}]')


class CommonServiceMixin(UnionServiceMixin, ComplexServiceMixin):
    pass


class SaasAlchemyService(SQLAlchemyService):

    def _query(self) -> LesoonQuery:
        query = super()._query()
        return query.filter_by(company_id=current_request.user.company_id)
