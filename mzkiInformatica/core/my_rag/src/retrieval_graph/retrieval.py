"""Manage the configuration of various retrievers.

This module provides functionality to create and manage retrievers for different
vector store backends, specifically Django database with pgvector.

The retrievers support filtering results by user_id to ensure data isolation between users.
"""

import os
from contextlib import contextmanager
from typing import Generator

from langchain_core.embeddings import Embeddings
from langchain_core.runnables import RunnableConfig
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_core.documents import Document

from .configuration import Configuration, IndexConfiguration

## Encoder constructors


def make_text_encoder(model: str) -> Embeddings:
    """Connect to the configured text encoder."""
    provider, model = model.split("/", maxsplit=1)
    match provider:
        case "openai":
            from langchain_openai import OpenAIEmbeddings

            return OpenAIEmbeddings(model=model)
        case "cohere":
            from langchain_cohere import CohereEmbeddings

            return CohereEmbeddings(model=model)  # type: ignore
        case _:
            raise ValueError(f"Unsupported embedding provider: {provider}")


## Retriever constructors


@contextmanager
def make_elastic_retriever(
    configuration: IndexConfiguration, embedding_model: Embeddings
) -> Generator[VectorStoreRetriever, None, None]:
    """Configure this agent to connect to a specific elastic index."""
    from langchain_elasticsearch import ElasticsearchStore

    connection_options = {}
    if configuration.retriever_provider == "elastic-local":
        connection_options = {
            "es_user": os.environ["ELASTICSEARCH_USER"],
            "es_password": os.environ["ELASTICSEARCH_PASSWORD"],
        }

    else:
        connection_options = {"es_api_key": os.environ["ELASTICSEARCH_API_KEY"]}

    vstore = ElasticsearchStore(
        **connection_options,  # type: ignore
        es_url=os.environ["ELASTICSEARCH_URL"],
        index_name="langchain_index",
        embedding=embedding_model,
    )

    search_kwargs = configuration.search_kwargs

    search_filter = search_kwargs.setdefault("filter", [])
    search_filter.append({"term": {"metadata.user_id": configuration.user_id}})
    yield vstore.as_retriever(search_kwargs=search_kwargs)


@contextmanager
def make_pinecone_retriever(
    configuration: IndexConfiguration, embedding_model: Embeddings
) -> Generator[VectorStoreRetriever, None, None]:
    """Configure this agent to connect to a specific pinecone index."""
    from langchain_pinecone import PineconeVectorStore

    search_kwargs = configuration.search_kwargs

    search_filter = search_kwargs.setdefault("filter", {})
    search_filter.update({"user_id": configuration.user_id})
    vstore = PineconeVectorStore.from_existing_index(
        os.environ["PINECONE_INDEX_NAME"], embedding=embedding_model
    )
    yield vstore.as_retriever(search_kwargs=search_kwargs)


@contextmanager
def make_mongodb_retriever(
    configuration: IndexConfiguration, embedding_model: Embeddings
) -> Generator[VectorStoreRetriever, None, None]:
    """Configure this agent to connect to a specific MongoDB Atlas index & namespaces."""
    from langchain_mongodb.vectorstores import MongoDBAtlasVectorSearch

    vstore = MongoDBAtlasVectorSearch.from_connection_string(
        os.environ["MONGODB_URI"],
        namespace="langgraph_retrieval_agent.default",
        embedding=embedding_model,
    )
    search_kwargs = configuration.search_kwargs
    pre_filter = search_kwargs.setdefault("pre_filter", {})
    pre_filter["user_id"] = {"$eq": configuration.user_id}
    yield vstore.as_retriever(search_kwargs=search_kwargs)


class DjangoDBRetriever:
    """Custom retriever for Django database with pgvector."""
    
    def __init__(self, embedding_model: Embeddings, search_kwargs: dict):
        self._embedding_model = embedding_model
        self._search_kwargs = search_kwargs
        self._k = search_kwargs.get("k", 10)
        self._similarity_threshold = search_kwargs.get("similarity_threshold", 0.5)
    
    def _get_relevant_documents(self, query: str) -> list[Document]:
        """Synchronous method to retrieve relevant documents."""
        return self._similarity_search(query)
    
    async def _aget_relevant_documents(self, query: str) -> list[Document]:
        """Asynchronous method to retrieve relevant documents."""
        from asgiref.sync import sync_to_async
        return await sync_to_async(self._similarity_search)(query)
    
    async def ainvoke(self, input: str, config=None) -> list[Document]:
        """Async invoke method for compatibility with LangChain."""
        return await self._aget_relevant_documents(input)
    
    def _similarity_search(self, query: str) -> list[Document]:
        """Perform similarity search in Django database using cosine similarity on JSON embeddings."""
        from django.conf import settings
        import django
        
        # Ensure Django is set up
        if not settings.configured:
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "escola.settings")
            django.setup()
        
        from core.models import CursoEmbeddingChunk
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Generate query embedding
        query_embedding = np.array(self._embedding_model.embed_query(query))
        
        # Fetch all chunks and compute similarity in Python
        chunks = CursoEmbeddingChunk.objects.select_related("curso").prefetch_related(
            "curso__modalidades", "curso__modulos"
        )
        
        # Calculate similarities
        similarities = []
        for chunk in chunks:
            try:
                chunk_embedding = np.array(chunk.embedding)
                # Compute cosine similarity
                similarity = cosine_similarity([query_embedding], [chunk_embedding])[0][0]
                similarities.append((chunk, similarity))
            except Exception as e:
                print(f"Erro ao processar embedding do chunk {chunk.id}: {e}")
                continue
        
        # Sort by similarity and filter by threshold
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Filter by threshold and limit to k results
        threshold_similarity = self._similarity_threshold
        filtered_results = [(chunk, sim) for chunk, sim in similarities if sim >= threshold_similarity][:self._k]
        
        # Convert to LangChain documents
        documents = []
        for chunk, similarity in filtered_results:
            curso = chunk.curso
            
            # Build metadata with course information
            metadata = {
                "curso_id": curso.id,
                "titulo": curso.titulo,
                "app": curso.app,
                "nivel": curso.nivel,
                "versao": curso.versao,
                "carga_horaria": curso.carga_horaria,
                "cor": curso.cor,
                "descricao_curta": curso.descricao_curta,
                "objetivos": curso.objetivos,
                "publico_alvo": curso.publico_alvo,
                "prerequisitos": curso.prerequisitos,
                "conteudo_programatico": curso.conteudo_programatico,
                "modalidades": [m.nome for m in curso.modalidades.all()],
                "modulos": [
                    {
                        "titulo": m.titulo,
                        "descricao": m.descricao,
                        "ordem": m.ordem,
                    }
                    for m in curso.modulos.all()
                ],
                "similarity_score": float(similarity),
                "fonte": chunk.fonte,
            }
            
            doc = Document(
                page_content=chunk.texto,
                metadata=metadata
            )
            documents.append(doc)
        
        return documents
        
        # Convert to LangChain documents
        documents = []
        for result in results:
            curso = result.curso
            
            # Build metadata with course information
            metadata = {
                "curso_id": curso.id,
                "titulo": curso.titulo,
                "app": curso.app,
                "nivel": curso.nivel,
                "versao": curso.versao,
                "carga_horaria": curso.carga_horaria,
                "cor": curso.cor,
                "descricao_curta": curso.descricao_curta,
                "objetivos": curso.objetivos,
                "publico_alvo": curso.publico_alvo,
                "prerequisitos": curso.prerequisitos,
                "conteudo_programatico": curso.conteudo_programatico,
                "modalidades": [m.nome for m in curso.modalidades.all()],
                "modulos": [
                    {
                        "titulo": m.titulo,
                        "descricao": m.descricao,
                        "ordem": m.ordem,
                    }
                    for m in curso.modulos.all()
                ],
                "similarity_score": float(1 - result.distance),
                "fonte": result.fonte,
            }
            
            doc = Document(
                page_content=result.texto,
                metadata=metadata
            )
            documents.append(doc)
        
        return documents


@contextmanager
def make_django_retriever(
    configuration: IndexConfiguration, embedding_model: Embeddings
) -> Generator[DjangoDBRetriever, None, None]:
    """Configure this agent to connect to Django database."""
    retriever = DjangoDBRetriever(
        embedding_model=embedding_model,
        search_kwargs=configuration.search_kwargs
    )
    yield retriever


@contextmanager
def make_retriever(
    config: RunnableConfig,
) -> Generator[DjangoDBRetriever, None, None]:
    """Create a retriever for the agent, based on the current configuration."""
    configuration = IndexConfiguration.from_runnable_config(config)
    embedding_model = make_text_encoder(configuration.embedding_model)
    
    match configuration.retriever_provider:
        case "django-db":
            with make_django_retriever(configuration, embedding_model) as retriever:
                yield retriever

        case "elastic" | "elastic-local":
            with make_elastic_retriever(configuration, embedding_model) as retriever:
                yield retriever

        case "pinecone":
            with make_pinecone_retriever(configuration, embedding_model) as retriever:
                yield retriever

        case "mongodb":
            with make_mongodb_retriever(configuration, embedding_model) as retriever:
                yield retriever

        case _:
            raise ValueError(
                "Unrecognized retriever_provider in configuration. "
                f"Expected one of: django-db, elastic, elastic-local, pinecone, mongodb\n"
                f"Got: {configuration.retriever_provider}"
            )
