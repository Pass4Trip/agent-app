import os

from lightrag import LightRAG, QueryParam
from lightrag.llm import gpt_4o_mini_complete


# def queryLightRAG(query,mode="hybrid"):
#     WORKING_DIR = "/Users/vinh/Documents/agent-app/RAG/vectorDB_persistance"

#     if not os.path.exists(WORKING_DIR):
#         os.mkdir(WORKING_DIR)

#     rag = LightRAG(
#         working_dir=WORKING_DIR,
#         llm_model_func=gpt_4o_mini_complete,
#         # llm_model_func=gpt_4o_complete
#     )


#     # with open("./resto.txt") as f:
#     #     rag.insert(f.read())

#     system_message="""  Tu es un assistant pour répondre aux questions de l'utilisateur.
#                         Soit concis, explicite et tu devra etre synthétique dans ta reponse.
#                         Tu ne dois ps générer de code ou proposer du code.
#                         Tu ne dois pas inventer des questions.
#                         Tu ne dois pas répondre si tu ne dispose pas de l'information.
#                         Avec ces consignes voici la demande de l'utilisateur :

#                     """


#     query = system_message + query

#     '''
#     # Perform hybrid search
#     print(
#         rag.query(query, param=QueryParam(mode="naive"))
#     )

#     # Perform hybrid search
#     print(
#         rag.query(query, param=QueryParam(mode="local"))
#     )

#     # Perform hybrid search
#     print(
#         rag.query(query, param=QueryParam(mode="global"))
#     )
#     '''

#     # Perform hybrid search
#     res = rag.query(query, param=QueryParam(mode=mode))
#     print(res)

#     return res


query = "liste moi les restaurants ou je peux manger dans le calme et avec des plats simples"

mode = "hybrid"


WORKING_DIR = "/Users/vinh/Documents/agent-app/RAG/vectorDB_persistance"

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

rag = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=gpt_4o_mini_complete,
    # llm_model_func=gpt_4o_complete
)


# with open("./resto.txt") as f:
#     rag.insert(f.read())

system_message = """  Tu es un assistant pour répondre aux questions de l'utilisateur.
                    Soit concis, explicite et tu devra etre synthétique dans ta reponse.
                    Tu ne dois ps générer de code ou proposer du code.
                    Tu ne dois pas inventer des questions.
                    Tu ne dois pas répondre si tu ne dispose pas de l'information.
                    Avec ces consignes voici la demande de l'utilisateur : 
                    
                """


query = system_message + query

"""
# Perform hybrid search
print(
    rag.query(query, param=QueryParam(mode="naive"))
)

# Perform hybrid search
print(
    rag.query(query, param=QueryParam(mode="local"))
)

# Perform hybrid search
print(
    rag.query(query, param=QueryParam(mode="global"))
)
"""

# Perform hybrid search
res = rag.query(query, param=QueryParam(mode=mode))
print(res)
