GRAPH_FIELD_SEP = "<SEP>"

PROMPTS = {}

PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|>"
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "##"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"
PROMPTS["process_tickers"] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

PROMPTS["DEFAULT_ENTITY_TYPES"] = [
    "restaurant",
    "adresse",
    "category",
    "positive_point",
    "negative_point",
    "recommandation",
]

PROMPTS["entity_extraction"] = """-Goal-
Given a text document that is potentially relevant to this activity and a list of entity types, identify all entities of those types from the text and all relationships among the identified entities.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, capitalized
- entity_type: One of the following types: [{entity_types}]
- entity_description: Comprehensive description of the entity's attributes and activities
Format each entity as ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity
- relationship_keywords: one or more high-level key words that summarize the overarching nature of the relationship, focusing on concepts or themes rather than specific details
Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)

3. Identify high-level key words that summarize the main concepts, themes, or topics of the entire text. These should capture the overarching ideas present in the document.
Format the content-level key words as ("content_keywords"{tuple_delimiter}<high_level_keywords>)

4. Return output in English as a single list of all the entities and relationships identified in steps 1 and 2. Use **{record_delimiter}** as the list delimiter.

5. When finished, output {completion_delimiter}

######################
-Examples-
######################
Example 1:

Entity_types: [restaurant, CID, category, positive_point, negative_point, recommandation]
Text:
Nom restaurant : Pizzeria Napoli
Categorie : Restaurant italien
CID: 7764700260837340345
Description : Pizzeria Napoli, un lieu convivial proposant une cuisine italienne authentique.  On apprécie généralement les pizzas, notamment la Margherita, qui est un classique.  Cependant, les prix peuvent être un peu élevés et il peut y avoir des files d'attente.
################
Output:
("entity"{tuple_delimiter}"Pizzeria Napoli"{tuple_delimiter}"restaurant"{tuple_delimiter}"Pizzeria Napoli, un lieu convivial proposant une cuisine italienne authentique."){record_delimiter}
("entity"{tuple_delimiter}"7764700260837340345"{tuple_delimiter}"CID"{tuple_delimiter}"Pizzeria Napoli est située à l'adresse 4 Rue du Commerce, 75011 Paris."){record_delimiter}
("entity"{tuple_delimiter}"Restaurant italien"{tuple_delimiter}"category"{tuple_delimiter}"Pizzeria Napoli est un restaurant de pizza traditionnelle."){record_delimiter}
("entity"{tuple_delimiter}"lieu convivial"{tuple_delimiter}"positive_point"{tuple_delimiter}"Le restaurant est considéré comme un lieu convivial."){record_delimiter}
("entity"{tuple_delimiter}"cuisine italienne authentique"{tuple_delimiter}"positive_point"{tuple_delimiter}"Le restaurant propose une cuisine italienne authentique."){record_delimiter}
("entity"{tuple_delimiter}"les prix peuvent être un peu élevés"{tuple_delimiter}"negative_point"{tuple_delimiter}"Le restaurant a des prix un peu élevés."){record_delimiter}
("entity"{tuple_delimiter}"il peut y avoir des files d'attente"{tuple_delimiter}"negative_point"{tuple_delimiter}"Le restaurant a parfois des files d'attente."){record_delimiter}
("entity"{tuple_delimiter}"Pizza Margherita"{tuple_delimiter}"recommandation"{tuple_delimiter}"On apprécie généralement les pizzas, notamment la Margherita, qui est un classique."){record_delimiter}

("relationship"{tuple_delimiter}"Pizzeria Napoli"{tuple_delimiter}"Pizzeria"{tuple_delimiter}"Le restaurant Pizzeria Napoli est de categorie Restaurant italien."{tuple_delimiter}"power dynamics, perspective shift"{tuple_delimiter}1){record_delimiter}
("relationship"{tuple_delimiter}"Pizzeria Napoli"{tuple_delimiter}"lieu convivial"{tuple_delimiter}"Pizzeria Napoli, un lieu convivial."{tuple_delimiter}"lieu convivial"{tuple_delimiter}1){record_delimiter}
("relationship"{tuple_delimiter}"Pizzeria Napoli"{tuple_delimiter}"cuisine italienne authentique"{tuple_delimiter}"Pizzeria Napoli, un restaurant proposant une cuisine italienne authentique."{tuple_delimiter}"cuisine italienne authentique"{tuple_delimiter}1){record_delimiter}
("relationship"{tuple_delimiter}"Pizzeria Napoli"{tuple_delimiter}"les prix peuvent être un peu élevés"{tuple_delimiter}"Cependant, les prix peuvent être un peu élevés ."{tuple_delimiter}"prix un peu élevé"{tuple_delimiter}1){record_delimiter}
("relationship"{tuple_delimiter}"Pizzeria Napoli"{tuple_delimiter}"il peut y avoir des files d'attente"{tuple_delimiter}"il peut y avoir des files d'attente."{tuple_delimiter}"files d'attente"{tuple_delimiter}1){record_delimiter}
("relationship"{tuple_delimiter}"Pizzeria Napoli"{tuple_delimiter}"Pizza Margherita"{tuple_delimiter}"Pizzeria Napoli propose son classique avec la pizza Margherita qui est un classique."{tuple_delimiter}"Pizza Margherita, classique"{tuple_delimiter}1){record_delimiter}
#############################
-Real Data-
######################
Entity_types: {entity_types}
Text: {input_text}
######################
Output:
"""

PROMPTS[
    "summarize_entity_descriptions"
] = """You are a helpful assistant responsible for generating a comprehensive summary of the data provided below.
Given one or two entities, and a list of descriptions, all related to the same entity or group of entities.
Please concatenate all of these into a single, comprehensive description. Make sure to include information collected from all the descriptions.
If the provided descriptions are contradictory, please resolve the contradictions and provide a single, coherent summary.
Make sure it is written in third person, and include the entity names so we the have full context.

#######
-Data-
Entities: {entity_name}
Description List: {description_list}
#######
Output:
"""

PROMPTS[
    "entiti_continue_extraction"
] = """MANY entities were missed in the last extraction.  Add them below using the same format:
"""

PROMPTS[
    "entiti_if_loop_extraction"
] = """It appears some entities may have still been missed.  Answer YES | NO if there are still entities that need to be added.
"""

PROMPTS["fail_response"] = "Sorry, I'm not able to provide an answer to that question."

PROMPTS["rag_response"] = """---Role---

You are a helpful assistant responding to questions about data in the tables provided.


---Goal---

Generate a response of the target length and format that responds to the user's question, summarizing all information in the input data tables appropriate for the response length and format, and incorporating any relevant general knowledge.
If you don't know the answer, just say so. Do not make anything up.
Do not include information where the supporting evidence for it is not provided.

---Target response length and format---

{response_type}

---Data tables---

{context_data}

Add sections and commentary to the response as appropriate for the length and format. Style the response in markdown.
"""

PROMPTS["keywords_extraction"] = """---Role---

You are a helpful assistant tasked with identifying both high-level and low-level keywords in the user's query.

---Goal---

Given the query, list both high-level and low-level keywords. High-level keywords focus on overarching concepts or themes, while low-level keywords focus on specific entities, details, or concrete terms.

---Instructions---

- Output the keywords in JSON format.
- The JSON should have two keys:
  - "high_level_keywords" for overarching concepts or themes.
  - "low_level_keywords" for specific entities or details.

######################
-Examples-
######################
Example 1:

Query: "How does international trade influence global economic stability?"
################
Output:
{{
  "high_level_keywords": ["International trade", "Global economic stability", "Economic impact"],
  "low_level_keywords": ["Trade agreements", "Tariffs", "Currency exchange", "Imports", "Exports"]
}}
#############################
Example 2:

Query: "What are the environmental consequences of deforestation on biodiversity?"
################
Output:
{{
  "high_level_keywords": ["Environmental consequences", "Deforestation", "Biodiversity loss"],
  "low_level_keywords": ["Species extinction", "Habitat destruction", "Carbon emissions", "Rainforest", "Ecosystem"]
}}
#############################
Example 3:

Query: "What is the role of education in reducing poverty?"
################
Output:
{{
  "high_level_keywords": ["Education", "Poverty reduction", "Socioeconomic development"],
  "low_level_keywords": ["School access", "Literacy rates", "Job training", "Income inequality"]
}}
#############################
-Real Data-
######################
Query: {query}
######################
Output:

"""

PROMPTS["naive_rag_response"] = """You're a helpful assistant
Below are the knowledge you know:
{content_data}
---
If you don't know the answer or if the provided knowledge do not contain sufficient information to provide an answer, just say so. Do not make anything up.
Generate a response of the target length and format that responds to the user's question, summarizing all information in the input data tables appropriate for the response length and format, and incorporating any relevant general knowledge.
If you don't know the answer, just say so. Do not make anything up.
Do not include information where the supporting evidence for it is not provided.
---Target response length and format---
{response_type}
"""
