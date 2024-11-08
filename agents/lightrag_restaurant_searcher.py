from typing import Optional
import json

from phi.agent import Agent
from phi.model.openai import OpenAIChat

from phi.knowledge.agent import AgentKnowledge
from phi.storage.agent.postgres import PgAgentStorage
from phi.vectordb.pgvector import PgVector, SearchType

from agents.settings import agent_settings
from db.session import db_url

from specifics.restaurant_RAG.lightrag import LightRAG, QueryParam
#from specifics.restaurant_RAG.lightrag.llm import gpt_4o_mini_complete


lightRAG_agent_storage = PgAgentStorage(table_name="lightRAG_agent_sessions", db_url=db_url)
lightRAG_agent_knowledge = AgentKnowledge(
    vector_db=PgVector(table_name="lightRAG_agent_knowledge", db_url=db_url, search_type=SearchType.hybrid)
)


def lightrag_query(query: str = "une recherche de restaurant a Lyon", mode="hybrid"):
    # ATTENTION VTT A VARIABILISER le path
    WORKING_DIR = "/app/RAG/vectorDB_persistance"

    rag = LightRAG(working_dir=WORKING_DIR, llm_model_func=gpt_4o_mini_complete)

    system_message = """  Tu es un assistant pour répondre aux questions de l'utilisateur.
                        Soit concis, explicite et tu devra etre synthétique dans ta reponse.
                        Tu ne dois ps générer de code ou proposer du code.
                        Tu ne dois pas inventer des questions.
                    """

    query = system_message + query

    # Perform hybrid search
    res = rag.query(query, param=QueryParam(mode=mode))

    json_res = []
    json_res.append(res)
    return json.dumps(json_res)


def get_lightrag_restaurant_searcher(
    model_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
) -> Agent:
    return Agent(
        name="LIGHTRAG Restaurant Searcher",
        agent_id="lightrag-restaurant-searcher",
        session_id=session_id,
        user_id=user_id,
        # The model to use for the agent
        model=OpenAIChat(
            id=model_id or agent_settings.gpt_4,
            max_tokens=agent_settings.default_max_completion_tokens,
            temperature=agent_settings.default_temperature,
        ),
        # model=Ollama(id="qwen2.5m:latest"),
        # Tools available to the agent
        tools=[lightrag_query],
        # A description of the agent that guides its overall behavior
        role="Tu es un agent d'une Team qui dispose des capacités à aider l'utilisateur à trouver un restaurant à Lyon. Tu es sollicité paar Agent Leader avec une demande précise. Tu utilisera uniquement les informations en provenance de la fonction rag_query pour trouver les restaurants à Lyon répondant aux critères de l'utilisateur. Tu dois renvoyer tes résultats à Agent Leader",
        # A list of instructions to follow, each as a separate item in the list
        instructions=[
            "Etape 1 : Analyser la demande de Agent Leader et utiliser uniquement les informations en provenance de la fonction rag_query pour trouver les restaurants à Lyon répondant aux critères de l'utilisateur.\n",
            "Etape 2 : Renvoyer les résultats dà Agent Leader .\n",
        ],
        # Format responses as markdown
        markdown=True,
        # Show tool calls in the response
        show_tool_calls=True,
        # Add the current date and time to the instructions
        add_datetime_to_instructions=True,
        # Store agent sessions in the database
        storage=lightRAG_agent_storage,
        # Enable read the chat history from the database
        read_chat_history=True,
        # Store knowledge in a vector database
        # knowledge=lightRAG_agent_knowledge,
        # Enable searching the knowledge base
        # search_knowledge=True,
        # Enable monitoring on phidata.app
        monitoring=True,
        # Show debug logs
        debug_mode=True,
    )
