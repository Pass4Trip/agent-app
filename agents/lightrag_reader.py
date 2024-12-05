from typing import Optional

from phi.agent import Agent
from phi.model.openai import OpenAIChat

from phi.knowledge.agent import AgentKnowledge
from phi.storage.agent.postgres import PgAgentStorage
from phi.vectordb.pgvector import PgVector, SearchType

from agents.settings import agent_settings
from db.session import db_url

from lightrag import LightRAG, QueryParam
from lightrag.llm import gpt_4o_mini_complete
from lightrag.utils import EmbeddingFunc

import requests
import numpy as np
import logging
import os
from time import sleep
from requests.exceptions import HTTPError, Timeout

import json


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


lightrag_reader_storage = PgAgentStorage(table_name="lightrag_reader_sessions", db_url=db_url)
lightrag_reader_knowledge = AgentKnowledge(
    vector_db=PgVector(table_name="lightrag_reader_knowledge", db_url=db_url, search_type=SearchType.hybrid)
)


def call_llm_api(self, url: str, payload: dict, headers: dict) -> dict:
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur API LLM: {str(e)}")
        if response.status_code == 500:
            logger.info("Erreur 500 détectée, attente avant retry...")
            sleep(5)  # Attente supplémentaire pour les erreurs 500
        raise


def call_embedding_api(self, url: str, text: str, headers: dict) -> np.ndarray:
    try:
        # Calculate dynamic timeout based on consecutive errors
        timeout = 30 * (self.backoff_factor ** self.consecutive_500_errors)
        
        # Add request ID for tracking
        request_id = os.urandom(8).hex()
        logger.info(f"Starting embedding request {request_id}")
        
        response = requests.post(url, data=text, headers=headers, timeout=timeout)
        
        if response.status_code == 500:
            self.consecutive_500_errors += 1
            logger.warning(f"HTTP 500 error (consecutive: {self.consecutive_500_errors})")
            
            if self.consecutive_500_errors >= self.max_consecutive_500_errors:
                logger.error("Circuit breaker triggered: too many consecutive 500 errors")
                raise Exception("Circuit breaker open: API service appears to be down")
            
            # Calculate adaptive sleep time
            sleep_time = 5 * (self.backoff_factor ** self.consecutive_500_errors)
            logger.info(f"Backing off for {sleep_time:.1f} seconds")
            sleep(sleep_time)
            
            raise HTTPError(f"HTTP 500 error on request {request_id}")
        
        response.raise_for_status()
        self.consecutive_500_errors = 0  # Reset on success
        return response.json()
        
    except Timeout:
        logger.error("Request timed out")
        raise
    except HTTPError as e:
        if e.response is not None:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise



def llm_model_func(
    prompt, system_prompt=None, history_messages=[], **kwargs
) -> str:
    url = "https://llama-3-1-70b-instruct.endpoints.kepler.ai.cloud.ovh.net/api/openai_compat/v1/chat/completions"
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "max_tokens": kwargs.get("max_tokens", 512),
        "messages": messages,
        "model": "Meta-Llama-3_1-70B-Instruct",
        "temperature": kwargs.get("temperature", 0),
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OVH_AI_ENDPOINTS_ACCESS_TOKEN')}",
    }
    
    response_data = call_llm_api(url, payload, headers)
    return response_data["choices"][0]["message"]["content"]

def embedding_func(texts: list[str]) -> np.ndarray:
    url = "https://multilingual-e5-base.endpoints.kepler.ai.cloud.ovh.net/api/text2vec"
    headers = {
        "Content-Type": "text/plain",
        "Authorization": f"Bearer {os.getenv('OVH_AI_ENDPOINTS_ACCESS_TOKEN')}",
    }
    
    embeddings = []
    for text in texts:
        embedding = call_embedding_api(url, text, headers)
        embeddings.append(embedding)
    
    return np.array(embeddings)




def lightrag_query(query: str = "une recherche de restaurants", mode="hybrid"):
    # ATTENTION VTT A VARIABILISER le path
    WORKING_DIR = "/app/RAG/vectorDB_persistance"

    # Initialiser LightRAG
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=llm_model_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=768,  # Dimension for multilingual-e5-base model
            max_token_size=8192,
            func=embedding_func
        ),
        kg="Neo4JStorage",
        log_level="INFO",
    )

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
    


def get_lightrag_reader(
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
        storage=lightrag_reader_storage,
        # Enable read the chat history from the database
        read_chat_history=True,
        # Store knowledge in a vector database
        knowledge=lightrag_reader_knowledge,
        # Enable searching the knowledge base
        #search_knowledge=True,
        # Enable monitoring on phidata.app
        monitoring=True,
        # Show debug logs
        debug_mode=True,
    )