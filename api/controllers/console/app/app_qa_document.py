# -*- coding:utf-8 -*-
from flask import request
from flask_login import current_user
from core.login.login import login_required
from flask_restful import Resource, fields, marshal, reqparse
from sqlalchemy import desc, asc
from werkzeug.exceptions import NotFound, Forbidden

import services
from controllers.console import api
from controllers.console.app.error import ProviderNotInitializeError
from controllers.console.datasets.error import HighQualityDatasetOnlyError
from controllers.console.setup import setup_required
from controllers.console.wraps import account_initialization_required
from core.model_providers.error import ProviderTokenNotInitError, LLMBadRequestError
from core.model_providers.model_factory import ModelFactory
from libs.helper import TimestampField
from models.model import AppQADocument
# from models.dataset import QADocument
# from services.dataset_service import DatasetService
from services.app_qa_document_service import QADocumentService
from controllers.console.app import _get_app

qa_document_fields = {
    'id': fields.String,
    'position': fields.Integer,
    'answer': fields.String,
    'question': fields.String,
    'enabled': fields.Boolean,
    'error': fields.String,
    'created_at': TimestampField,
}

class QADocumentResource(Resource):
    def get_qa_document(self, app_id: str, qa_document_id: str, mode: str = None) -> AppQADocument:
        app = _get_app(app_id, mode)
        qa_document = QADocumentService.get_qa_document(app.id, qa_document_id)

        if not qa_document:
            raise NotFound('QA Document not found.')

        return qa_document


class QADatasetDocumentListApi(QADocumentResource):
    @setup_required
    @login_required
    @account_initialization_required
    def get(self, app_id):
        app_id = str(app_id)
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=20, type=int)
        search = request.args.get('keyword', default=None, type=str)
        sort = request.args.get('sort', default='-created_at', type=str)
        fetch = request.args.get('fetch', default=False, type=bool)
        app = _get_app(app_id)

        query = AppQADocument.query.filter_by(
            app_id=str(app.id))
        
        if search:
            search = f'%{search}%'
            query = query.filter(AppQADocument.answer.like(search))

        if sort.startswith('-'):
            sort_logic = desc
            sort = sort[1:]
        else:
            sort_logic = asc
            
        if sort == 'created_at':
            query = query.order_by(sort_logic(AppQADocument.created_at))
        else:
            query = query.order_by(desc(AppQADocument.created_at))
            
        paginated_qa_documents = query.paginate(
            page=page, per_page=limit, max_per_page=100, error_out=False)
        qa_documents = paginated_qa_documents.items

        data = marshal(qa_documents, qa_document_fields)
        response = {
            'data': data,
            'has_more': len(qa_documents) == limit,
            'limit': limit,
            'total': paginated_qa_documents.total,
            'page': page
        }

        return response
    
    @setup_required
    @login_required
    @account_initialization_required
    def post(self, app_id):
        # check app_id
        app_id = str(app_id)
        app = _get_app(app_id)
        app_model_config = app.app_model_config
        
        # check embedding model setting
        try:
            ModelFactory.get_embedding_model(
                tenant_id=current_user.current_tenant_id,
                model_provider_name=app_model_config.embedding_model_provider,
                model_name=app_model_config.embedding_model
            )
        except LLMBadRequestError:
            raise ProviderNotInitializeError(
                f"No Embedding Model available. Please configure a valid provider "
                f"in the Settings -> Model Provider.")
        except ProviderTokenNotInitError as ex:
            raise ProviderNotInitializeError(ex.description)
        
        # validate args
        parser = reqparse.RequestParser()
        parser.add_argument('answer', type=str, required=True, nullable=False, location='json')
        parser.add_argument('question', type=str, required=True, nullable=False, location='json')
        args = parser.parse_args()
        QADocumentService.qa_document_create_args_validate(args)
        qa_document = QADocumentService.create_qa_document(args, app)
        return {
            'data': marshal(qa_document, qa_document_fields)
        }, 200

class QADocumentApi(QADocumentResource):
    @setup_required
    @login_required
    @account_initialization_required
    def get(self, app_id, qa_document_id):
        app_id = str(app_id)
        qa_document_id = str(qa_document_id)
        qa_document = self.get_qa_document(app_id, qa_document_id)

        response = marshal(qa_document, qa_document_fields)
        return response
        
    @setup_required
    @login_required
    @account_initialization_required
    def put(self, app_id, qa_document_id):
        app_id = str(app_id)
        qa_document_id = str(qa_document_id)
        
        qa_document = self.get_qa_document(app_id, qa_document_id)
        if not qa_document:
            raise NotFound('Document not found.')
        
        app = _get_app(app_id)
        app_model_config = app.app_model_config
        # check embedding model setting
        try:
            ModelFactory.get_embedding_model(
                tenant_id=current_user.current_tenant_id,
                model_provider_name=app_model_config.embedding_model_provider,
                model_name=app_model_config.embedding_model
            )
        except LLMBadRequestError:
            raise ProviderNotInitializeError(
                f"No Embedding Model available. Please configure a valid provider "
                f"in the Settings -> Model Provider.")
        except ProviderTokenNotInitError as ex:
            raise ProviderNotInitializeError(ex.description)
        
        # validate args
        parser = reqparse.RequestParser()
        parser.add_argument('answer', type=str, required=True, nullable=False, location='json')
        parser.add_argument('question', type=str, required=True, nullable=False, location='json')
        args = parser.parse_args()
        QADocumentService.qa_document_create_args_validate(args)
        qa_document = QADocumentService.update_qa_document(args, qa_document, app)
        return {
            'data': marshal(qa_document, qa_document_fields)
        }, 200
        
    @setup_required
    @login_required
    @account_initialization_required
    def delete(self, app_id, qa_document_id):
        app_id = str(app_id)
        qa_document_id = str(qa_document_id)
        qa_document = self.get_qa_document(app_id, qa_document_id)
        if not qa_document:
            raise NotFound('Document not found.')
        # The role of the current user in the ta table must be admin or owner
        if current_user.current_tenant.current_role not in ['admin', 'owner']:
            raise Forbidden()
        
        app = _get_app(app_id)
        app_model_config = app.app_model_config
        # check embedding model setting
        try:
            ModelFactory.get_embedding_model(
                tenant_id=current_user.current_tenant_id,
                model_provider_name=app_model_config.embedding_model_provider,
                model_name=app_model_config.embedding_model
            )
        except LLMBadRequestError:
            raise ProviderNotInitializeError(
                f"No Embedding Model available. Please configure a valid provider "
                f"in the Settings -> Model Provider.")
        except ProviderTokenNotInitError as ex:
            raise ProviderNotInitializeError(ex.description)
        
        QADocumentService.delete_qa_document(qa_document, app)
        return {'result': 'success'}, 200
    
api.add_resource(QADatasetDocumentListApi,
                 '/apps/<uuid:app_id>/qa_documents')

api.add_resource(QADocumentApi,
                 '/apps/<uuid:app_id>/qa_documents/<uuid:qa_document_id>')
