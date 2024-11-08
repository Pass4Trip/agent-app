from phi.agent import Agent
from phi.tools.crawl4ai_tools import Crawl4aiTools

from typing import Optional

from phi.model.openai import OpenAIChat
from phi.model.ollama import Ollama

from phi.knowledge.agent import AgentKnowledge
from phi.storage.agent.postgres import PgAgentStorage
from phi.vectordb.pgvector import PgVector, SearchType
from phi.knowledge.json import JSONKnowledgeBase

from agents.settings import agent_settings
from db.session import db_url

import json
from pathlib import Path

import os
from os import getenv
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy

OPENAI_API_KEY = getenv("OPENAI_API_KEY") 


db_url = "postgresql+psycopg://ai:ai@localhost:5432/ai"
crawl4ai_agent_storage = PgAgentStorage(table_name="crawl4ai_agent_sessions", db_url=db_url)
crawl4ai_agent_knowledge = AgentKnowledge(
    vector_db=PgVector(table_name="crawl4ai_agent_knowledge", db_url=db_url, search_type=SearchType.hybrid)
)


def Crawl4aiLocalTools(url: str = "une url à crawler"):
    async def extract_tech_content(url):
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(
                url=url,
                extraction_strategy=LLMExtractionStrategy(
                    provider="openai/gpt-4o-mini",
                    api_token=OPENAI_API_KEY,
                    instruction="Extrait moi les événements avec une description synthétique en une phrase courte, le lieu et la date",
                ),
                bypass_cache=True,
            )

        tech_content = json.loads(result.extracted_content)
        print(f"Number of tech-related items extracted: {len(tech_content)}")

        with open(
            "/Users/vinh/Documents/agent-app/trend_RAG/sortiraparis.com/rag.json", "w", encoding="utf-8"
        ) as f:
            json.dump(tech_content, f, indent=2)

    asyncio.run(extract_tech_content(url))


# Crawl4aiLocalTools("https://www.sortiraparis.com/loisirs/salon")

sortiraparis_knowledge_base = JSONKnowledgeBase(
    path=Path("/Users/vinh/Documents/agent-app/trend_RAG/sortiraparis.com/"),
    vector_db=PgVector(table_name="sortiraparis", db_url=db_url),
)
