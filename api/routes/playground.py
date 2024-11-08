from os import getenv
from phi.playground import Playground

from agents.agent_leader import get_agent_leader
from agents.web_searcher import get_web_searcher
#from agents.lightrag_restaurant_searcher import get_lightrag_restaurant_searcher
#from agents.crawl4ai import get_crawl4ai_searcher
from agents.agent_trello import get_trello_agent
######################################################
## Router for the agent playground
######################################################
agent_leader = get_agent_leader(debug_mode=True)
web_searcher = get_web_searcher(debug_mode=True)
#lightrag_restaurant_searcher = get_lightrag_restaurant_searcher(debug_mode=True)
#crawl4ai_searcher = get_crawl4ai_searcher(debug_mode=True)
trello_agent = get_trello_agent(debug_mode=True)

# Create a playground instance
playground = Playground(
    agents=[agent_leader, web_searcher, trello_agent]
)

# Log the playground endpoint with phidata.app
if getenv("RUNTIME_ENV") == "dev":
    playground.create_endpoint("http://localhost:8000")

playground_router = playground.get_router()
