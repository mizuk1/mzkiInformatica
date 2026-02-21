"""Main entrypoint for the conversational retrieval graph.

This module defines the core structure and functionality of the course
recommendation retrieval graph. It includes the main graph definition, state management,
and key functions for processing user inputs, generating queries, retrieving
relevant courses, and formulating personalized recommendations.
"""

import json
from datetime import datetime, timezone
from typing import cast

from langchain_core.documents import Document
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field

from . import retrieval
from .configuration import Configuration
from .state import InputState, State
from .utils import get_message_text, load_chat_model

# Define the function that calls the model


class SearchQueries(BaseModel):
    """Search queries for finding relevant courses."""

    queries: list[str] = Field(
        description="List of 1-3 specific search queries to find relevant courses. Each query should focus on a single concept or skill."
    )


class CursoRecommendationAI(BaseModel):
    """AI analysis of a course: only curso_id and AI-generated comments.
    
    The LLM should ONLY choose from existing courses (curso_id from the provided list)
    and generate ordem_trilha, motivo_trilha, and comentario_ia.
    All other fields (titulo, app, nivel, etc) come from the database.
    """
    
    curso_id: int = Field(
        description="ID of the course from the provided list. MUST be one of the curso_id values from CURSOS DISPONÍVEIS."
    )
    ordem_trilha: int = Field(
        description="Order in the learning path (1, 2, 3, etc.). Lower numbers are prerequisites/should be done first."
    )
    motivo_trilha: str = Field(
        description="Why this course is in this position in the learning path (2-3 sentences max)"
    )
    comentario_ia: str = Field(
        description="Personalized comment explaining how this specific course helps the user achieve their goal and what they will learn (2-4 sentences max)"
    )


class CursoRecommendations(BaseModel):
    """List of course recommendations with learning path.
    
    IMPORTANT: Only select courses from the provided list (use existing curso_id).
    DO NOT create new courses or invent curso_id that don't exist.
    """
    
    recomendacoes: list[CursoRecommendationAI] = Field(
        description="List of recommended courses ordered by learning path. ONLY use curso_id from the provided CURSOS DISPONÍVEIS list."
    )
    resumo_trilha: str = Field(
        description="Brief summary of the learning path: why these courses and in this order (2-3 sentences)"
    )


async def generate_query(
    state: State, *, config: RunnableConfig
) -> dict[str, list[str]]:
    """Generate search queries based on the user's message.

    This function analyzes the user's message and generates one or more specific
    search queries. For simple questions, it generates a single query. For complex
    questions, it breaks them down into multiple sub-queries (max 3).

    Args:
        state (State): The current state containing messages.
        config (RunnableConfig): Configuration for the query generation process.

    Returns:
        dict[str, list[str]]: A dictionary with 'queries' key containing generated queries.
    """
    configuration = Configuration.from_runnable_config(config)
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", configuration.query_system_prompt),
            ("placeholder", "{messages}"),
        ]
    )
    model = load_chat_model(configuration.query_model).with_structured_output(
        SearchQueries
    )

    message_value = await prompt.ainvoke(
        {
            "messages": state.messages,
            "queries": "\n- ".join(state.queries) if state.queries else "None",
            "system_time": datetime.now(tz=timezone.utc).isoformat(),
        },
        config,
    )
    generated = cast(SearchQueries, await model.ainvoke(message_value, config))
    return {
        "queries": generated.queries,
    }


async def retrieve(
    state: State, *, config: RunnableConfig
) -> dict[str, list[Document] | list[dict]]:
    """Retrieve documents based on all queries in the state.

    This function takes the current state and configuration, uses all queries
    from the state to retrieve relevant documents using the retriever, and returns
    the retrieved documents (deduplicated by curso_id) along with their JSON representation.

    Args:
        state (State): The current state containing queries.
        config (RunnableConfig): Configuration for the retrieval process.

    Returns:
        dict: A dictionary with:
            - "retrieved_docs": list of unique retrieved Document objects
            - "cursos_json": list of dictionaries with course information for the LLM
    """
    all_docs = []
    seen_curso_ids = set()
    cursos_json = []
    
    with retrieval.make_retriever(config) as retriever:
        # Search with each query
        for query in state.queries:
            response = await retriever._aget_relevant_documents(query)
            
            # Deduplicate by curso_id
            for doc in response:
                curso_id = doc.metadata.get("curso_id")
                if curso_id and curso_id not in seen_curso_ids:
                    all_docs.append(doc)
                    seen_curso_ids.add(curso_id)
                    
                    # Build course JSON for LLM analysis
                    curso_info = {
                        "curso_id": curso_id,
                        "titulo": doc.metadata.get("titulo"),
                        "app": doc.metadata.get("app"),
                        "nivel": doc.metadata.get("nivel"),
                        "versao": doc.metadata.get("versao"),
                        "carga_horaria": doc.metadata.get("carga_horaria"),
                        "descricao_curta": doc.metadata.get("descricao_curta"),
                        "objetivos": doc.metadata.get("objetivos", ""),
                        "publico_alvo": doc.metadata.get("publico_alvo", ""),
                        "prerequisitos": doc.metadata.get("prerequisitos", ""),
                        "modalidades": doc.metadata.get("modalidades", []),
                        "modulos": doc.metadata.get("modulos", []),
                        "similarity_score": doc.metadata.get("similarity_score", 0),
                    }
                    cursos_json.append(curso_info)
    
    return {"retrieved_docs": all_docs, "cursos_json": cursos_json}


async def generate_recommendations(
    state: State, *, config: RunnableConfig
) -> dict:
    """Generate personalized recommendations for all retrieved courses.

    This function analyzes ALL retrieved courses together and:
    1. Decides which are ideal for the user
    2. Orders them in a logical learning path (prerequisites first)
    3. Explains why each course is in that position
    4. Generates personalized comments for each course

    The LLM returns a structured list with all courses analyzed at once,
    allowing it to create a coherent learning path.

    Args:
        state (State): The current state containing messages and cursos_json.
        config (RunnableConfig): Configuration for the response generation.

    Returns:
        dict: A dictionary with 'curso_results' containing a list of course recommendations
              with learning path order and personalized comments.
    """
    if not state.cursos_json:
        return {"curso_results": []}
    
    configuration = Configuration.from_runnable_config(config)
    
    # Get user's original message
    user_message = get_message_text(state.messages[0]) if state.messages else ""
    
    # Prepare all courses as JSON for the LLM
    cursos_json_str = json.dumps(state.cursos_json, ensure_ascii=False, indent=2)
    
    # Create a focused prompt that gives the LLM ALL courses at once
    analysis_prompt = f"""Você está analisando TODOS estes cursos para recomendação a um usuário.

🚨 REGRA FUNDAMENTAL: APENAS escolha cursos que estão na lista "CURSOS DISPONÍVEIS" abaixo.
   - Use APENAS os curso_id que aparecem na lista
   - NÃO invente novos cursos
   - NÃO crie curso_id que não existem
   - Se não houver cursos suficientes, retorne apenas os disponíveis

Sua tarefa é:
1. SELECIONAR quais cursos (pelo curso_id) são relevantes para o usuário
2. ORDENAR os cursos em uma TRILHA DE APRENDIZADO lógica
3. Para CADA curso escolhido, gerar:
   - curso_id: use o ID EXATO da lista abaixo (OBRIGATÓRIO)
   - ordem_trilha: posição na trilha (1, 2, 3, ...)
   - motivo_trilha: por que este curso é importante NESTA posição (2-3 frases)
   - comentario_ia: como ajuda o usuário alcançar seu objetivo (2-4 frases)

DIRETRIZES da trilha:
- Básico/Essencial → Intermediário → Avançado
- Cada curso prepara para o próximo
- Máximo 5-8 cursos (qualidade > quantidade)
- Se houver poucos cursos disponíveis, retorne todos que forem relevantes

CURSOS DISPONÍVEIS (use APENAS estes curso_id):
{cursos_json_str}

MENSAGEM DO USUÁRIO:
{user_message}

⚠️ LEMBRE-SE: Use APENAS os curso_id da lista CURSOS DISPONÍVEIS acima. Não invente cursos novos."""
    
    # Create messages directly (avoiding template variable issues with JSON)
    system_message = SystemMessage(content=configuration.response_system_prompt)
    user_message_obj = HumanMessage(content=analysis_prompt)
    
    model = load_chat_model(configuration.response_model).with_structured_output(
        CursoRecommendations
    )
    
    # Single call to LLM with all courses
    message_value = [system_message, user_message_obj]
    
    response = await model.ainvoke(message_value, config)
    recommendations = cast(CursoRecommendations, response)
    
    # Create lookup dict for fast curso_id -> course data mapping
    cursos_lookup = {curso["curso_id"]: curso for curso in state.cursos_json}
    
    # JOIN: Combine LLM analysis with real course data (with deduplication)
    curso_results = []
    seen_curso_ids = set()
    
    for rec in recommendations.recomendacoes:
        # Skip if we already added this curso_id (deduplication)
        if rec.curso_id in seen_curso_ids:
            continue
        
        # Get real course data from the database
        curso_data = cursos_lookup.get(rec.curso_id)
        
        if not curso_data:
            # Skip if LLM hallucinated a course_id that doesn't exist
            continue
        
        # Mark this curso_id as seen
        seen_curso_ids.add(rec.curso_id)
        
        # Merge: real data + LLM analysis
        curso_result = {
            # Real course data from database
            "curso_id": curso_data["curso_id"],
            "titulo": curso_data["titulo"],
            "app": curso_data["app"],
            "nivel": curso_data["nivel"],
            "versao": curso_data["versao"],
            "carga_horaria": curso_data["carga_horaria"],
            "descricao_curta": curso_data["descricao_curta"],
            "modalidades": curso_data["modalidades"],
            "similarity_score": curso_data.get("similarity_score", 0),
            # AI-generated analysis
            "ordem_trilha": rec.ordem_trilha,
            "motivo_trilha": rec.motivo_trilha,
            "comentario_ia": rec.comentario_ia,
        }
        curso_results.append(curso_result)
    
    return {"curso_results": curso_results}


# Define the graph


builder = StateGraph(State, input_schema=InputState, config_schema=Configuration)

builder.add_node(generate_query)  # type: ignore[arg-type]
builder.add_node(retrieve)  # type: ignore[arg-type]
builder.add_node(generate_recommendations)  # type: ignore[arg-type]
builder.add_edge("__start__", "generate_query")
builder.add_edge("generate_query", "retrieve")
builder.add_edge("retrieve", "generate_recommendations")

# Finally, we compile it!
# This compiles it into a graph you can invoke and deploy.
graph = builder.compile(
    interrupt_before=[],
    interrupt_after=[],
)
graph.name = "CourseRecommendationGraph"