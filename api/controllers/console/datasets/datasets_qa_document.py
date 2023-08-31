# -*- coding:utf-8 -*-
import random
from datetime import datetime
from typing import List

from flask import request, current_app
from flask_login import current_user
from core.login.login import login_required
from flask_restful import Resource, fields, marshal, marshal_with, reqparse
from sqlalchemy import desc, asc
from werkzeug.exceptions import NotFound, Forbidden

import services
from controllers.console import api
from controllers.console.app.error import ProviderNotInitializeError, ProviderQuotaExceededError, \
    ProviderModelCurrentlyNotSupportError
from controllers.console.datasets.error import DocumentAlreadyFinishedError, InvalidActionError, DocumentIndexingError, \
    InvalidMetadataError, ArchivedDocumentImmutableError, HighQualityDatasetOnlyError
from controllers.console.setup import setup_required
from controllers.console.wraps import account_initialization_required
from core.indexing_runner import IndexingRunner
from core.model_providers.error import ProviderTokenNotInitError, QuotaExceededError, ModelCurrentlyNotSupportError, \
    LLMBadRequestError
from core.model_providers.model_factory import ModelFactory
from extensions.ext_redis import redis_client
from libs.helper import TimestampField
from extensions.ext_database import db
from models.dataset import DatasetProcessRule, Dataset
from models.dataset import QADocument, DocumentSegment
from models.model import UploadFile
from services.dataset_service import QADocumentService, DatasetService
from tasks.add_document_to_index_task import add_document_to_index_task
from tasks.remove_document_from_index_task import remove_document_from_index_task

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
    def get_qa_document(self, dataset_id: str, qa_document_id: str) -> QADocument:
        dataset = DatasetService.get_dataset(dataset_id)
        if not dataset:
            raise NotFound('Dataset not found.')

        try:
            DatasetService.check_dataset_permission(dataset, current_user)
        except services.errors.account.NoPermissionError as e:
            raise Forbidden(str(e))

        qa_document = QADocumentService.get_qa_document(dataset_id, qa_document_id)

        if not qa_document:
            raise NotFound('QA Document not found.')

        if qa_document.tenant_id != current_user.current_tenant_id:
            raise Forbidden('No permission.')

        return qa_document


class QADatasetDocumentListApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def get(self, dataset_id):
        dataset_id = str(dataset_id)
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=20, type=int)
        search = request.args.get('keyword', default=None, type=str)
        sort = request.args.get('sort', default='-created_at', type=str)
        fetch = request.args.get('fetch', default=False, type=bool)
        dataset = DatasetService.get_dataset(dataset_id)
        if not dataset:
            raise NotFound('Dataset not found.')
        
        try:
            DatasetService.check_dataset_permission(dataset, current_user)
        except services.errors.account.NoPermissionError as e:
            raise Forbidden(str(e))

        query = QADocument.query.filter_by(
            dataset_id=str(dataset_id), tenant_id=current_user.current_tenant_id)
        
        if search:
            search = f'%{search}%'
            query = query.filter(QADocument.answer.like(search))

        if sort.startswith('-'):
            sort_logic = desc
            sort = sort[1:]
        else:
            sort_logic = asc
            
        if sort == 'created_at':
            query = query.order_by(sort_logic(QADocument.created_at))
        else:
            query = query.order_by(desc(QADocument.created_at))
            
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
    def post(self, dataset_id):
        # check dataset
        dataset_id = str(dataset_id)
        dataset = DatasetService.get_dataset(dataset_id)
        if not dataset:
            raise NotFound('Dataset not found.')
        
        if dataset.indexing_technique != 'high_quality':
            raise HighQualityDatasetOnlyError()
        
        # The role of the current user in the ta table must be admin or owner
        if current_user.current_tenant.current_role not in ['admin', 'owner']:
            raise Forbidden()
        
        # check embedding model setting
        try:
            ModelFactory.get_embedding_model(
                tenant_id=current_user.current_tenant_id,
                model_provider_name=dataset.embedding_model_provider,
                model_name=dataset.embedding_model
            )
        except LLMBadRequestError:
            raise ProviderNotInitializeError(
                f"No Embedding Model available. Please configure a valid provider "
                f"in the Settings -> Model Provider.")
        except ProviderTokenNotInitError as ex:
            raise ProviderNotInitializeError(ex.description)
        
        try:
            DatasetService.check_dataset_permission(dataset, current_user)
        except services.errors.account.NoPermissionError as e:
            raise Forbidden(str(e))
        # validate args
        parser = reqparse.RequestParser()
        parser.add_argument('answer', type=str, required=True, nullable=False, location='json')
        parser.add_argument('question', type=str, required=True, nullable=False, location='json')
        args = parser.parse_args()
        QADocumentService.qa_document_create_args_validate(args)
        qa_document = QADocumentService.create_qa_document(args, dataset)
        return {
            'data': marshal(qa_document, qa_document_fields)
        }, 200

class QADocumentApi(QADocumentResource):
    @setup_required
    @login_required
    @account_initialization_required
    def get(self, dataset_id, qa_document_id):
        dataset_id = str(dataset_id)
        qa_document_id = str(qa_document_id)
        qa_document = self.get_qa_document(dataset_id, qa_document_id)

        response = marshal(qa_document, qa_document_fields)
        return response
        
    @setup_required
    @login_required
    @account_initialization_required
    def put(self, dataset_id, qa_document_id):
        # check dataset
        dataset_id = str(dataset_id)
        dataset = DatasetService.get_dataset(dataset_id)
        if not dataset:
            raise NotFound('Dataset not found.')
        
        if dataset.indexing_technique != 'high_quality':
            raise HighQualityDatasetOnlyError()
        
        # check document
        qa_document_id = str(qa_document_id)
        qa_document = self.get_qa_document(dataset_id, qa_document_id)
        if not qa_document:
            raise NotFound('Document not found.')
        # The role of the current user in the ta table must be admin or owner
        if current_user.current_tenant.current_role not in ['admin', 'owner']:
            raise Forbidden()
        
        # check embedding model setting
        try:
            ModelFactory.get_embedding_model(
                tenant_id=current_user.current_tenant_id,
                model_provider_name=dataset.embedding_model_provider,
                model_name=dataset.embedding_model
            )
        except LLMBadRequestError:
            raise ProviderNotInitializeError(
                f"No Embedding Model available. Please configure a valid provider "
                f"in the Settings -> Model Provider.")
        except ProviderTokenNotInitError as ex:
            raise ProviderNotInitializeError(ex.description)
        
        try:
            DatasetService.check_dataset_permission(dataset, current_user)
        except services.errors.account.NoPermissionError as e:
            raise Forbidden(str(e))
        # validate args
        parser = reqparse.RequestParser()
        parser.add_argument('answer', type=str, required=True, nullable=False, location='json')
        parser.add_argument('question', type=str, required=True, nullable=False, location='json')
        args = parser.parse_args()
        QADocumentService.qa_document_create_args_validate(args)
        qa_document = QADocumentService.update_qa_document(args, qa_document, dataset)
        return {
            'data': marshal(qa_document, qa_document_fields)
        }, 200
        
    @setup_required
    @login_required
    @account_initialization_required
    def delete(self, dataset_id, qa_document_id):
        # check dataset
        dataset_id = str(dataset_id)
        dataset = DatasetService.get_dataset(dataset_id)
        if not dataset:
            raise NotFound('Dataset not found.')
        # check user's model setting
        DatasetService.check_dataset_model_setting(dataset)
        # check document
        qa_document_id = str(qa_document_id)
        qa_document = self.get_qa_document(dataset_id, qa_document_id)
        if not qa_document:
            raise NotFound('Document not found.')
        # The role of the current user in the ta table must be admin or owner
        if current_user.current_tenant.current_role not in ['admin', 'owner']:
            raise Forbidden()
        
        # check embedding model setting
        try:
            ModelFactory.get_embedding_model(
                tenant_id=current_user.current_tenant_id,
                model_provider_name=dataset.embedding_model_provider,
                model_name=dataset.embedding_model
            )
        except LLMBadRequestError:
            raise ProviderNotInitializeError(
                f"No Embedding Model available. Please configure a valid provider "
                f"in the Settings -> Model Provider.")
        except ProviderTokenNotInitError as ex:
            raise ProviderNotInitializeError(ex.description)
        
        try:
            DatasetService.check_dataset_permission(dataset, current_user)
        except services.errors.account.NoPermissionError as e:
            raise Forbidden(str(e))

        try:
            DatasetService.check_dataset_permission(dataset, current_user)
        except services.errors.account.NoPermissionError as e:
            raise Forbidden(str(e))
        QADocumentService.delete_qa_document(qa_document, dataset)
        return {'result': 'success'}, 200
    
api.add_resource(QADatasetDocumentListApi,
                 '/datasets/<uuid:dataset_id>/qa_documents')

api.add_resource(QADocumentApi,
                 '/datasets/<uuid:dataset_id>/qa_documents/<uuid:qa_document_id>')
