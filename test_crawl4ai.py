from phi.agent import Agent
from crawl4ai_pgVector import sortiraparis_knowledge_base


agent = Agent(
    knowledge=sortiraparis_knowledge_base,
    add_references_to_prompt=True,
)
agent.knowledge.load(recreate=False)

agent.print_response("liste moi 3 salons a venir sur Paris")
