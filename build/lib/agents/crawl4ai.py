from phi.agent import Agent

from typing import Optional

from phi.model.openai import OpenAIChat

from phi.knowledge.agent import AgentKnowledge
from phi.storage.agent.postgres import PgAgentStorage
from phi.vectordb.pgvector import PgVector, SearchType

from agents.settings import agent_settings
from db.session import db_url

import json
from pathlib import Path

import os
from crawl4ai_pgVector import sortiraparis_knowledge_base

print(db_url)
#db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"
#crawl4ai_agent_storage = PgAgentStorage(table_name="crawl4ai_agent_sessions", db_url=db_url)
#crawl4ai_agent_knowledge = AgentKnowledge(vector_db=PgVector(table_name="sortiraparis", db_url=db_url,  search_type=SearchType.vector))

#crawl4ai_agent_knowledge.load(recreate=False) 

def get_crawl4ai_searcher(
    model_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
) -> Agent:
    
    agent = Agent(
        name="Crawl4ai",
        agent_id="agent-crawl4ai",
        session_id=session_id,
        user_id=user_id,
        # The model to use for the agent
        model=OpenAIChat(
            id=model_id or agent_settings.gpt_4,
            max_tokens=agent_settings.default_max_completion_tokens,
            temperature=agent_settings.default_temperature,
        ), 
        role="Tu es un agent d'une Team qui dispose des connaissances du site internet https://www.sortiraparis.com/loisirs/salon",   
        instructions=[
            "Etape 1 : Utiliser tes connaissances pour répondre aux question de l'utilisateur.\n",
            "Etape 2 : Renvoyer les résultats à Agent Leader .\n",             
            ],
        add_datetime_to_instructions=True,
        markdown=True,
        # Show tool calls in the response
        show_tool_calls=True,
        # Add the current date and time to the instructions
        # Store agent sessions in the database
        #storage=crawl4ai_agent_storage,
        # Enable read the chat history from the database
        #read_chat_history=True,
        # Store knowledge in a vector database
        knowledge=sortiraparis_knowledge_base,
        add_references_to_prompt=True,
        # Enable searching the knowledge base
        search_knowledge=False,
        # Enable monitoring on phidata.app
        monitoring=True,
        # Show debug logs
        debug_mode=True,
    )
    return agent

