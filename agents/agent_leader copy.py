from typing import Optional

from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.model.ollama import Ollama

from phi.knowledge.agent import AgentKnowledge
from phi.storage.agent.postgres import PgAgentStorage
from phi.tools.duckduckgo import DuckDuckGo
from phi.vectordb.pgvector import PgVector, SearchType

from agents.settings import agent_settings
from db.session import db_url


from RAG.lightrag import LightRAG, QueryParam
from RAG.lightrag.llm import gpt_4o_mini_complete
from RAG.lightrag import LightRAG
import json

agent_leader_storage = PgAgentStorage(table_name="agent_leader_sessions", db_url=db_url)
agent_leader_knowledge = AgentKnowledge(
    vector_db=PgVector(table_name="agent_leader_knowledge", db_url=db_url, search_type=SearchType.hybrid)
)


def rag_query(query: str = "chercher un restaurant a Lyon", mode="hybrid"):
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


def get_rag_restaurant_searcher(
    model_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
) -> Agent:
    return Agent(
        name="RAG Restaurant Searcher",
        agent_id="rag-restaurant-searcher",
        session_id=session_id,
        user_id=user_id,
        # The model to use for the agent
        model=Ollama(id="llama3.2"),
        # model=Ollama(id="qwen2.5m:latest"),
        # Tools available to the agent
        tools=[rag_query],
        # A description of the agent that guides its overall behavior
        description="Si l'utilisateur recherche un restaurant à Lyon alors tu devra lui répondreTen tant que un expert AI agent avec un accès à une fonction rag_query qui te permet de répondre à des questions sur les restaurants à Lyon.", 
        # A list of instructions to follow, each as a separate item in the list
        instructions=[
            "Always user answer from your fucntion rag_query for any question links to restaurants in Lyon.\n"
            "  - Provide answers based function rag_query whenever possible.",        ],
        # Format responses as markdown
        markdown=True,
        # Show tool calls in the response
        show_tool_calls=True,
        # Add the current date and time to the instructions
        add_datetime_to_instructions=True,
        # Store agent sessions in the database
        #storage=example_agent_storage,
        # Enable read the chat history from the database
        #read_chat_history=True,
        # Store knowledge in a vector database
        #knowledge=example_agent_knowledge,
        # Enable searching the knowledge base
        #search_knowledge=True,
        # Enable monitoring on phidata.app
        monitoring=True,
        # Show debug logs
        debug_mode=debug_mode,
    )


 
def get_web_restaurant_searcher(
    model_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
) -> Agent:
    return Agent(
        name="Web Searcher",
        agent_id="web-restaurant-searcher",
        session_id=session_id,
        user_id=user_id,
        # The model to use for the agent
        model=Ollama(id="llama3.2"),
        role="Tu es un expert d'internet et tu donnera les informations pour répondre aux questions autres que les restaurants à Lyon qui sont à la charge de RAG Restaurant Searcher.", 
        description="You are a Web Search Agent that has the special skill of searching the web for information and presenting the results in a structured manner for restaurants not located in Lyon.",
        instructions=[
            "To answer the user's question, first search the web for information by breaking down the user's question into smaller queries.",
            "Make sure you cover all the aspects of the question.",
            "Important: \n"
            " - Focus on legitimate sources\n"
            " - Always provide sources and the links to the information you used to answer the question\n"
            " - If you cannot find the answer, say so and ask the user to provide more details.",
            "Keep your answers concise and engaging.", 
        ],
        tools=[DuckDuckGo()],
        add_datetime_to_instructions=True,
        markdown=True,
        # Show tool calls in the response
        show_tool_calls=True,
        # Add the current date and time to the instructions
        # Store agent sessions in the database
        #storage=example_agent_storage,
        # Enable read the chat history from the database
        #read_chat_history=True
        # Store knowledge in a vector database
        #knowledge=example_agent_knowledge,
        # Enable searching the knowledge base
        #search_knowledge=True,
        # Enable monitoring on phidata.app
        monitoring=True,
        # Show debug logs
        debug_mode=debug_mode,
    )



def get_agent_leader(
    model_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
) -> Agent:
    return Agent(
        name="Agent Leader",
        agent_id="agent-leader",
        session_id=session_id,
        user_id=user_id,
        # The model to use for the agent
        model=Ollama(id="llama3.2"),
        team=[get_rag_restaurant_searcher, get_rag_restaurant_searcher],
        description="Tu es un expert AI et Leader d'un team d'agent pour répondre aux questions concernant les restaurants de lyon. Tu dispose de 2 experts pour t'aider à repondre aux questions de l'utilisateur : - rag_restaurant_searcher qui te donnera les informations pour réponse à des questions sur les restaurants à Lyon. - web_restaurant_searcher qui te permet de répondre aux questions autres que les restaurants de Lyon.",
        instructions=[
            "First, demande à o'utilisateur ce qu'il veut savoir.",
            "Si la question porte sur une questions de restaurant à Lyon alors demande à RAG Restaurant Searcher de répondre à la question.",
            "Si la question porte sur autre chose qu'une question de restaurant à Lyon alors demande à Web Searcher de répondre à la question.",
        ],     
        # Format responses as markdown
        markdown=True,
        # Show tool calls in the response
        show_tool_calls=True,
        # Add the current date and time to the instructions
        add_datetime_to_instructions=True,
        # Store agent sessions in the database
        storage=agent_leader_storage,
        # Enable read the chat history from the database
        read_chat_history=True,
        # Store knowledge in a vector database
        knowledge=agent_leader_knowledge,
        # Enable searching the knowledge base
        search_knowledge=True,
        # Enable monitoring on phidata.app
        monitoring=True,
        # Show debug logs
        debug_mode=debug_mode,
    )
