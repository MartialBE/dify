import logging
from typing import Optional, List
from extensions.ext_database import db
from sqlalchemy import func
from models.model import AppQADocument as QADocument, App
from models.dataset import Dataset, Document, DatasetQuery, DatasetProcessRule, AppDatasetJoin, DocumentSegment
from services.vector_service import VectorService


class QADocumentService:
    @staticmethod
    def get_qa_document(app_id: str, qa_document_id: str) -> Optional[QADocument]:
        qa_document = db.session.query(QADocument).filter(
            QADocument.id == qa_document_id,
            QADocument.app_id == app_id
        ).first()

        return qa_document

    # @staticmethod
    # def get_qa_document_by_id(qa_document_id: str) -> Optional[Document]:
    #     qa_document = db.session.query(QADocument).filter(
    #         QADocument.id == qa_document_id
    #     ).first()

    #     return qa_document

    # @staticmethod
    # def get_qa_document_by_dataset_id(dataset_id: str) -> List[Document]:
    #     qa_document = db.session.query(QADocument).filter(
    #         QADocument.dataset_id == dataset_id,
    #         QADocument.enabled == True
    #     ).all()

    #     return qa_document
    
    @classmethod
    def qa_document_create_args_validate(cls, args: dict):
        if 'answer' not in args or not args['answer'] or not args['answer'].strip():
            raise ValueError("answer is empty")
        if 'question' not in args or not args['question'] or not args['question'].strip():
            raise ValueError("question is empty")
    
    @classmethod
    def create_qa_document(cls, args: dict, app: App):
        
        max_position = db.session.query(func.max(QADocument.position)).filter(
            QADocument.app_id == app.id
        ).scalar()
        
        qa_document = QADocument(
            app_id=app.id,
            answer=args['answer'],
            question=args['question'],
            position=max_position + 1 if max_position else 1,
        )

        db.session.add(qa_document)
        db.session.commit()

        # save vector index
        try:
            VectorService.create_qa_document_vector(qa_document, app)
        except Exception as e:
            logging.exception("create qa document index failed:" + str(e))
            qa_document.enabled = False
            qa_document.error = str(e)
            db.session.commit()

        return qa_document
    
    @classmethod
    def update_qa_document(cls, args: dict, qa_document: QADocument, app: App):
        
        if args['answer'] == qa_document.answer and args['question'] == qa_document.question and qa_document.enabled:
            return qa_document
        
        qa_document.answer = args['answer']
        qa_document.question = args['question']
        db.session.add(qa_document)
        db.session.commit()
        
        # update vector index
        try:
            VectorService.update_qa_document_vector(qa_document, app)
        except Exception as e:
            logging.exception("update qa document index failed:" + str(e))
            qa_document.enabled = False
            qa_document.error = str(e)
            db.session.commit()

        return qa_document
    
    @classmethod
    def delete_qa_document(cls, qa_document: QADocument, app: App):
        # delete vector index
        try:
            VectorService.delete_qa_document_vector(qa_document, app)
        except Exception as e:
            logging.exception("delete qa document index failed:" + str(e))
            qa_document.enabled = False
            qa_document.error = str(e)
            db.session.commit()
            return
        db.session.delete(qa_document)
        db.session.commit()