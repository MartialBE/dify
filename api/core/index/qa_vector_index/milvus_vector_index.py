from typing import Optional, cast

from langchain.embeddings.base import Embeddings
from langchain.schema import Document, BaseRetriever
from langchain.vectorstores import VectorStore, milvus
from pydantic import BaseModel, root_validator

from core.index.base import BaseIndex
from core.index.qa_vector_index.base import BaseVectorIndex
from core.vector_store.milvus_vector_store import MilvusVectorStore
from core.vector_store.weaviate_vector_store import WeaviateVectorStore
from models.model import AppModelConfig, AppQADocument


class MilvusConfig(BaseModel):
    endpoint: str
    user: str
    password: str
    batch_size: int = 100

    @root_validator()
    def validate_config(cls, values: dict) -> dict:
        if not values['endpoint']:
            raise ValueError("config MILVUS_ENDPOINT is required")
        if not values['user']:
            raise ValueError("config MILVUS_USER is required")
        if not values['password']:
            raise ValueError("config MILVUS_PASSWORD is required")
        return values


class MilvusVectorIndex(BaseVectorIndex):
    def __init__(self, app_config: AppModelConfig, config: MilvusConfig, embeddings: Embeddings):
        super().__init__(app_config, embeddings)
        self._client = self._init_client(config)

    def get_type(self) -> str:
        return 'milvus'

    def get_index_name(self, app_config: AppModelConfig) -> str:
        if self.app_config.qa_index_struct_dict:
            class_prefix: str = self.app_config.qa_index_struct_dict['vector_store']['class_prefix']
            if not class_prefix.endswith('_qa'):
                # original class_prefix
                class_prefix += '_qa'

            return class_prefix

        app_id = app_config.app_id
        return "Vector_index_" + app_id.replace("-", "_") + '_qa'


    def to_index_struct(self) -> dict:
        return {
            "type": self.get_type(),
            "vector_store": {"class_prefix": self.get_index_name(self.app_config)}
        }

    def create(self, texts: list[Document], **kwargs) -> BaseIndex:
        uuids = self._get_uuids(texts)
        self._vector_store = WeaviateVectorStore.from_documents(
            texts,
            self._embeddings,
            client=self._client,
            index_name=self.get_index_name(self.app_config),
            uuids=uuids,
            by_text=False
        )

        return self

    def _get_vector_store(self) -> VectorStore:
        """Only for created index."""
        if self._vector_store:
            return self._vector_store

        attributes = ['doc_id', 'document_id', 'app_id', 'qa_answer']
        if self._is_origin():
            attributes = ['doc_id']

        return WeaviateVectorStore(
            client=self._client,
            index_name=self.get_index_name(self.app_config),
            text_key='text',
            embedding=self._embeddings,
            attributes=attributes,
            by_text=False
        )

    def _get_vector_store_class(self) -> type:
        return MilvusVectorStore

    def delete_by_document_id(self, document_id: str):
        if self._is_origin():
            self.recreate_dataset(self.app_config)
            return

        vector_store = self._get_vector_store()
        vector_store = cast(self._get_vector_store_class(), vector_store)

        vector_store.del_texts({
            "operator": "Equal",
            "path": ["doc_id"],
            "valueText": document_id
        })

    def _is_origin(self):
        if self.app_config.qa_index_struct_dict:
            class_prefix: str = self.app_config.qa_index_struct_dict['vector_store']['class_prefix']
            if not class_prefix.endswith('_Node'):
                # original class_prefix
                return True

        return False
