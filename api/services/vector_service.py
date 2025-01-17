
from typing import Optional, List

from langchain.schema import Document

from core.index.index import IndexBuilder

from models.dataset import Dataset, DocumentSegment

from models.model import App, AppQADocument


class VectorService:

    @classmethod
    def create_segment_vector(cls, keywords: Optional[List[str]], segment: DocumentSegment, dataset: Dataset):
        document = Document(
            page_content=segment.content,
            metadata={
                "doc_id": segment.index_node_id,
                "doc_hash": segment.index_node_hash,
                "document_id": segment.document_id,
                "dataset_id": segment.dataset_id,
            }
        )

        # save vector index
        index = IndexBuilder.get_index(dataset, 'high_quality')
        if index:
            index.add_texts([document], duplicate_check=True)

        # save keyword index
        index = IndexBuilder.get_index(dataset, 'economy')
        if index:
            if keywords and len(keywords) > 0:
                index.create_segment_keywords(segment.index_node_id, keywords)
            else:
                index.add_texts([document])

    @classmethod
    def update_segment_vector(cls, keywords: Optional[List[str]], segment: DocumentSegment, dataset: Dataset):
        # update segment index task
        vector_index = IndexBuilder.get_index(dataset, 'high_quality')
        kw_index = IndexBuilder.get_index(dataset, 'economy')
        # delete from vector index
        if vector_index:
            vector_index.delete_by_ids([segment.index_node_id])

        # delete from keyword index
        kw_index.delete_by_ids([segment.index_node_id])

        # add new index
        document = Document(
            page_content=segment.content,
            metadata={
                "doc_id": segment.index_node_id,
                "doc_hash": segment.index_node_hash,
                "document_id": segment.document_id,
                "dataset_id": segment.dataset_id,
            }
        )

        # save vector index
        if vector_index:
            vector_index.add_texts([document], duplicate_check=True)

        # save keyword index
        if keywords and len(keywords) > 0:
            kw_index.create_segment_keywords(segment.index_node_id, keywords)
        else:
            kw_index.add_texts([document])

    @classmethod
    def create_qa_document_vector(cls, qa_document: AppQADocument, app: App):
        document = Document(
            page_content=qa_document.question,
            metadata={
                "doc_id": qa_document.id,
                "document_id": qa_document.id,
                "app_id": qa_document.app_id,
                "qa_answer": qa_document.answer,
            }
        )

        # save vector index
        index = IndexBuilder.get_qa_index(app)
        if index:
            index.add_texts([document], duplicate_check=True)
            
    @classmethod
    def update_qa_document_vector(cls, qa_document: AppQADocument, app: App):
        vector_index = IndexBuilder.get_qa_index(app)
        vector_index.delete_by_document_id(qa_document.id)
        
        document = Document(
            page_content=qa_document.question,
            metadata={
                "doc_id": qa_document.id,
                "document_id": qa_document.id,
                "app_id": qa_document.app_id,
                "qa_answer": qa_document.answer,
            }
        )
        
        vector_index.add_texts([document], duplicate_check=True)
        
    @classmethod
    def delete_qa_document_vector(cls, qa_document: AppQADocument, app: App):
        vector_index = IndexBuilder.get_qa_index(app)
        vector_index.delete_by_document_id(qa_document.id)