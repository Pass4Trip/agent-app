from typing import Optional
import json

from phi.agent import Agent
from phi.model.openai import OpenAIChat
#from phi.model.ollama import Ollama

from phi.knowledge.agent import AgentKnowledge
from phi.storage.agent.postgres import PgAgentStorage
from phi.vectordb.pgvector import PgVector, SearchType
from phi.agent import AgentMemory
from phi.memory.db.postgres import PgMemoryDb

from agents.settings import agent_settings
from db.session import db_url

from agents.lightrag_restaurant_searcher import get_lightrag_restaurant_searcher
from agents.web_searcher import get_web_searcher
from agents.crawl4ai import get_crawl4ai_searcher
from agents.agent_trello import get_trello_agent


agent_leader_storage = PgAgentStorage(table_name="agent_leader_sessions", db_url=db_url)
agent_leader_knowledge = AgentKnowledge(vector_db=PgVector(table_name="agent_leader_knowledge", db_url=db_url, search_type=SearchType.hybrid))


# test push github

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
        model=OpenAIChat(
            id=model_id or agent_settings.gpt_4,
            max_tokens=agent_settings.default_max_completion_tokens,
            temperature=agent_settings.default_temperature,
        ),
        #team=[get_lightrag_restaurant_searcher(), get_web_searcher(), get_crawl4ai_searcher(), get_trello_agent()],
        team=[get_web_searcher(), get_trello_agent()],
        description="Tu es le Team Leader d'une team d'agent pour répondre aux demandes de l'utilisateur.",
        # instructions=[
        #     "Etape 1 : Analyser la demande de l'utilisateur.\n",
        #     "Etape 2 : Utiliser ta mémoire et les conversations passées pour trouver les informations qui peuvent etre utile pour apporter plus de précision à la demande de l'utilisateur.\n",
        #     " - Exemple : Si l'utiisateur rechercher un restaurant et que tu identifie que l'utilisateur apprécie le vin. Alors tu ajoutera à la demande initiale cette information et rechercher en bonus un restaurant avec du bon vin.\n",
        #     "Etape 2bis : Si l'utilisateur demande la création d'une nouvelle carte alors utilise l'Agent Trell de ta Team qui est capable d'interagir avec Trello.\n",
        #     "Etape 3 : Identifier si il y a besoin de transférer la demande à un agent de ta Team le plus approprié à traiter la demande.\n",
        #     " - Liste des agents de ta Team pour traiter des demandes spécifiques :\n",
        #     "    - LIGHTRAG Restaurant Searcher : Si l'utilisateur pose une question sur un restaurant de Lyon alors utilise cet agent de ta Team qui est capable de rechercher des informations sur les restaurants à Lyon.\n",
        #     "    - Web Searcher : Si l'utilisateur pose une question ayant besoin d'une informzation fraiche ou du webalors utilise cet agent de ta Team qui est capable de rechercher des informations sur le Web.\n",
        #     "    - Crawl4ai_crawl : Si l'utilisateur pose des questions sur les événements de type Salon à Paris alors utilise cet agent de ta Team qui est capable rechercher dans ses connaissances des informations du site internet https://www.sortiraparis.com/loisirs/salon.\n",
        #     "Etape 4 : Attendre le retour des agents de ta Team sollictés.\n",
        #     "Etape 5 : Une fois que l'agent sollicité te retourne le résultat et pour répondre à l'utilisateur.\n",
        #     "Etape 6 : Si tu as utilisé des informations de ta mémoire ou des conversations passées, mentionne le moi dans ta réponse.\n",
        #     " - Exemple : Si l'utiisateur rechercher un restaurant et que tu sais que j'apprécie le calme alors mentionne le : J'ai pris e, compte que tu apprécies le calme alors j'ai intégré dans ma recherche ce critère meme si tu ne me l'as pas précisé dans ta demande.\n",
        # ],
        instructions=[
            "Etape 1 : Analyser la demande de l'utilisateur.\n",
            "Etape 2 : Utiliser ta mémoire et les conversations passées pour trouver les informations qui peuvent etre utile pour apporter plus de précision à la demande de l'utilisateur.\n",
            "Etape 3 : Identifier si il y a besoin de transférer la demande à un agent de ta Team le plus approprié à traiter la demande.\n",
            " - Liste des agents de ta Team pour traiter des demandes spécifiques :\n",
            "    - Agent Trello : Si l'utilisateur demande la création d'une nouvelle carte Trello alors utilise l'Agent Trello de ta Team qui est capable d'interagir avec Trello.\n",
            "    - Web Searcher : Si l'utilisateur pose une question ayant besoin d'une informzation fraiche ou du webalors utilise cet agent de ta Team qui est capable de rechercher des informations sur le Web.\n",
            "Etape 4 : Attendre le retour des agents de ta Team sollictés.\n",
            "Etape 5 : Une fois que l'agent sollicité te retourne le résultat et pour répondre à l'utilisateur.\n",
            "Etape 6 : Si tu as utilisé des informations de ta mémoire ou des conversations passées, mentionne le moi dans ta réponse.\n",
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
        # search_knowledge=True,
        # Enable monitoring on phidata.app
        monitoring=True,
        # Show debug logs
        debug_mode=debug_mode,
        add_transfer_instructions=True,
        create_user_memories=True,
        create_session_summary=True,
        memory=AgentMemory(
            db=PgMemoryDb(table_name="agent_leader_memory", db_url=db_url),
            create_user_memories=True,
            create_session_summary=True,
        ),
    )