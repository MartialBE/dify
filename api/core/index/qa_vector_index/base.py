import json
import logging
from abc import abstractmethod
from typing import List, Any, cast

from langchain.embeddings.base import Embeddings
from langchain.schema import Document, BaseRetriever
from langchain.vectorstores import VectorStore
from weaviate import UnexpectedStatusCodeException

from core.index.base import BaseIndex
from extensions.ext_database import db
from models.model import AppModelConfig, AppQADocument


class BaseVectorIndex(BaseIndex):

    def __init__(self, app_config: AppModelConfig, embeddings: Embeddings):
        self.app_config = app_config
        self._embeddings = embeddings
        self._vector_store = None

    def get_type(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_index_name(self, app_config: AppModelConfig) -> str:
        raise NotImplementedError

    @abstractmethod
    def to_index_struct(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def _get_vector_store(self) -> VectorStore:
        raise NotImplementedError

    @abstractmethod
    def _get_vector_store_class(self) -> type:
        raise NotImplementedError

    def search(
            self, query: str,
            **kwargs: Any
    ) -> List[Document]:
        vector_store = self._get_vector_store()
        vector_store = cast(self._get_vector_store_class(), vector_store)

        search_type = kwargs.get('search_type') if kwargs.get('search_type') else 'similarity'
        search_kwargs = kwargs.get('search_kwargs') if kwargs.get('search_kwargs') else {}

        if search_type == 'similarity_score_threshold':
            score_threshold = search_kwargs.get("score_threshold")
            if (score_threshold is None) or (not isinstance(score_threshold, float)):
                search_kwargs['score_threshold'] = .95

            docs_with_similarity = vector_store.similarity_search_with_relevance_scores(
                query, **search_kwargs
            )

            docs = []
            for doc, similarity in docs_with_similarity:
                doc.metadata['score'] = similarity
                docs.append(doc)

            return docs

        # similarity k
        # mmr k, fetch_k, lambda_mult
        # similarity_score_threshold k
        return vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        ).get_relevant_documents(query)

    def get_retriever(self, **kwargs: Any) -> BaseRetriever:
        vector_store = self._get_vector_store()
        vector_store = cast(self._get_vector_store_class(), vector_store)

        return vector_store.as_retriever(**kwargs)

    def add_texts(self, texts: list[Document], **kwargs):
        if self._is_origin():
            self.recreate_dataset(self.app_config)

        vector_store = self._get_vector_store()
        vector_store = cast(self._get_vector_store_class(), vector_store)

        if kwargs.get('duplicate_check', False):
            texts = self._filter_duplicate_texts(texts)

        uuids = self._get_uuids(texts)
        vector_store.add_documents(texts, uuids=uuids)

    def text_exists(self, id: str) -> bool:
        vector_store = self._get_vector_store()
        vector_store = cast(self._get_vector_store_class(), vector_store)

        return vector_store.text_exists(id)

    def delete_by_ids(self, ids: list[str]) -> None:
        if self._is_origin():
            self.recreate_dataset(self.app_config)
            return

        vector_store = self._get_vector_store()
        vector_store = cast(self._get_vector_store_class(), vector_store)

        for node_id in ids:
            vector_store.del_text(node_id)

    def delete(self) -> None:
        vector_store = self._get_vector_store()
        vector_store = cast(self._get_vector_store_class(), vector_store)

        vector_store.delete()

    def _is_origin(self):
        return False

    def recreate_dataset(self, app_config: AppModelConfig):
        logging.info(f"Recreating app_config {app_config.id}")

        try:
            self.delete()
        except UnexpectedStatusCodeException as e:
            if e.status_code != 400:
                # 400 means index not exists
                raise e

        qa_documents = db.session.query(AppQADocument).filter(
            AppQADocument.app_id == app_config.app_id,
            AppQADocument.enabled == True,
        ).all()

        documents = []
        for qa_document in qa_documents:
            document = Document(
                page_content=qa_document.question,
                metadata={
                    "doc_id": qa_document.id,
                    "document_id": qa_document.id,
                    "app_id": qa_document.app_id,
                    "qa_answer": qa_document.answer,
                }
            )
            documents.append(document)

        origin_index_struct = self.app_config.qa_index_struct[:]
        self.app_config.qa_index_struct = None

        if documents:
            try:
                self.create(documents)
            except Exception as e:
                self.app_config.qa_index_struct = origin_index_struct
                raise e

            app_config.qa_index_struct = json.dumps(self.to_index_struct())

        db.session.commit()

        self.app_config = app_config
        logging.info(f"Dataset {app_config.id} recreate successfully.")

    def create_qdrant_dataset(self, app_config: AppModelConfig):
        logging.info(f"create_qdrant_dataset {app_config.id}")

        try:
            self.delete()
        except UnexpectedStatusCodeException as e:
            if e.status_code != 400:
                # 400 means index not exists
                raise e

        qa_documents = db.session.query(AppQADocument).filter(
            AppQADocument.app_id == app_config.app_id,
            AppQADocument.enabled == True,
        ).all()

        documents = []
        for qa_document in qa_documents:
            document = Document(
                page_content=qa_document.question,
                metadata={
                    "doc_id": qa_document.id,
                    "document_id": qa_document.id,
                    "app_id": qa_document.app_id,
                    "qa_answer": qa_document.answer,
                }
            )
            documents.append(document)

        if documents:
            try:
                self.create(documents)
            except Exception as e:
                raise e

        logging.info(f"Dataset {app_config.id} recreate successfully.")

    def update_qdrant_dataset(self, app_config: AppModelConfig):
        logging.info(f"update_qdrant_dataset {app_config.id}")

        qa_document = db.session.query(AppQADocument).filter(
            AppQADocument.app_id == app_config.app_id,
            AppQADocument.enabled == True,
        ).first()


        if qa_document:
            try:
                exist = self.text_exists(qa_document.id)
                if exist:
                    index_struct = {
                        "type": 'qdrant',
                        "vector_store": {"class_prefix": app_config.qa_index_struct_dict['vector_store']['class_prefix']}
                    }
                    app_config.qa_index_struct_dict = json.dumps(index_struct)
                    db.session.commit()
            except Exception as e:
                raise e

        logging.info(f"Dataset {app_config.id} recreate successfully.")
