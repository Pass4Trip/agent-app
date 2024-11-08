from typing import Optional

from phi.agent import Agent
from phi.model.openai import OpenAIChat

from phi.knowledge.agent import AgentKnowledge
from phi.storage.agent.postgres import PgAgentStorage
from phi.vectordb.pgvector import PgVector, SearchType

from agents.settings import agent_settings
from db.session import db_url

import requests
import json
import difflib
from pprint import pprint
from datetime import datetime, timedelta
import sqlite3
from os import getenv

from pydantic import BaseModel, Field


trello_agent_storage = PgAgentStorage(table_name="lightRAG_agent_sessions", db_url=db_url)

# API Credentials


chemins_a_garder = [["name"], ["labels", "name"], ["idMembers"], ["idLabels"], ["desc"], ["due"], ["idList"]]


class trello_card(BaseModel):
    card_name: str = Field(..., description="Nom du chantier associé à la carte.")
    card_label_name: str = Field(
        ..., description="Nom de la societe qui gère les actions à réaliser pour la carte."
    )
    # card_idLabels: str = Field(..., description="ID de la societe qui gère les actions à réaliser pour la carte.")
    card_list_name: str = Field(..., description="Nom de la liste dans laquelle la crate doit etre déposée.")
    # card_members_names: str = Field(..., description="Nom des personnes contributeurs de cette carte.")
    card_due_date: str = Field(..., description="Date d'échéance de la carte.")
    card_desc: str = Field(..., description="Description de la carte.")


def create_card(
    card_list_name: str = "none",
    card_name: str = "none",
    card_desc: str = "none",
    card_due_date: str = "none",
    card_label_name: str = "none",
):
    """
    Crée une carte Trello avec les informations fournies.
    """
    url = "https://api.trello.com/1/cards"

    headers = {"Accept": "application/json"}

    if card_list_name == "A FAIRE":
        idList = "671f465317b79fd50be2e628"
    elif card_list_name == "EN COURS":
        idList = "671f4658ef3675b58116fba2"
    elif card_list_name == "TERMINE":
        idList = "671f465d5576a36e7be95181"

    idlabels = "671f418c6bc19633db8649f7"

    query = {
        "idList": idList,
        "key": key,
        "token": token,
        "name": card_name,
        "desc": card_desc,
        #'idMembers': idmembers,
        "due": card_due_date,
        "idLabels": idlabels,
    }

    response = requests.post(url, headers=headers, params=query)
    # print(f"Réponse de création de carte: {response.status_code} - {response.text}")  # Log pour debug
    return response.json()


def delete_card(id_card, key, token):
    """
    Supprime une carte Trello spécifiée par son ID.
    """
    url = f"https://api.trello.com/1/cards/{id_card}"

    query = {"key": key, "token": token}

    response = requests.delete(url, params=query)
    # print(f"Réponse de suppression de carte: {response.status_code} - {response.text}")  # Log pour debug


def get_member(id_members, key, token):
    """
    Récupère les informations d'un membre Trello spécifié par son ID.
    """
    url = f"https://api.trello.com/1/members/{id_members}"

    headers = {"Accept": "application/json"}

    query = {"key": key, "token": token}

    response = requests.get(url, headers=headers, params=query)
    # print(f"Réponse pour récupération de membre {id_members}: {response.status_code} - {response.text}")  # Log pour debug
    return response.json().get("fullName", "Unknown")


def get_card(id_card, key, token):
    """
    Récupère les informations d'une carte Trello spécifiée par son ID.
    """
    url = f"https://api.trello.com/1/cards/{id_card}"

    headers = {"Accept": "application/json"}

    query = {"key": key, "token": token}

    response = requests.get(url, headers=headers, params=query)
    # print(f"Réponse pour récupération de carte {id_card}: {response.status_code} - {response.text}")  # Log pour debug
    return response.json()


def get_cards_from_lists(id_list, key, token):
    """
    Récupère toutes les cartes d'une liste Trello spécifiée par son ID.
    """
    url = f"https://api.trello.com/1/lists/{id_list}/cards"

    headers = {"Accept": "application/json"}

    query = {"key": key, "token": token}

    response = requests.get(url, headers=headers, params=query)
    # print(f"Réponse pour récupération des cartes de la liste {id_list}: {response.status_code} - {response.text}")  # Log pour debug
    return response.json()


def get_lists(id_list, key, token):
    """
    Récupère les informations d'une liste Trello spécifiée par son ID.
    """
    url = f"https://api.trello.com/1/lists/{id_list}"

    headers = {"Accept": "application/json"}

    query = {"key": key, "token": token}

    response = requests.get(url, headers=headers, params=query)
    # print(f"Réponse pour récupération de liste {id_list}: {response.status_code} - {response.text}")  # Log pour debug
    return response.json()


def transformer_json_entree(json_objet):
    """
    Transforme un dictionnaire JSON en remontant l'attribut 'name' dans 'labels' à la racine sous 'label_name',
    tout en conservant les autres attributs au même niveau.

    Paramètre :
    - json_objet (dict) : Le dictionnaire JSON d'entrée.

    Retourne :
    - dict : Un nouveau dictionnaire avec 'label_name' à la racine si 'name' dans 'labels' existe.
    """
    resultat = json_objet.copy()  # Copie pour ne pas modifier l'entrée originale

    # Extraire le 'name' de 'labels' s'il est présent et l'ajouter en tant que 'label_name' à la racine
    if "labels" in json_objet and isinstance(json_objet["labels"], list):
        for label in json_objet["labels"]:
            if "card_name" in label:
                resultat["card_label_name"] = label["card_name"]
                break  # On sort de la boucle après avoir trouvé le premier nom

    # Supprimer 'labels' de l'objet résultant pour ne pas le dupliquer
    resultat.pop("labels", None)

    return resultat


def filtrer_attributs_par_chemin(json_objet, chemins_a_garder, key, token):
    """
    Filtre un dictionnaire JSON imbriqué pour extraire les attributs spécifiés par des chemins précis.
    """
    resultat = {}

    for chemin in chemins_a_garder:
        sous_dictionnaire = json_objet
        sous_resultat = resultat
        for i, cle in enumerate(chemin):
            if isinstance(sous_dictionnaire, dict) and cle in sous_dictionnaire:
                if i == len(chemin) - 1:
                    if cle == "idMembers":
                        resultat["card_members_names"] = [
                            get_member(member_id, key, token) for member_id in sous_dictionnaire[cle]
                        ]
                    elif cle == "idList":
                        list_data = get_lists(sous_dictionnaire[cle], key, token)
                        resultat["card_list_name"] = list_data.get("name", "Unknown")
                    elif cle == "name":
                        sous_resultat["card_name"] = sous_dictionnaire[cle]
                    elif cle == "labels":
                        sous_resultat["labels"] = sous_dictionnaire[cle]
                    elif cle == "idLabels":
                        sous_resultat["card_idLabels"] = sous_dictionnaire[cle]
                    elif cle == "desc":
                        sous_resultat["card_desc"] = sous_dictionnaire[cle]
                    elif cle == "due":
                        sous_resultat["card_due_date"] = sous_dictionnaire[cle]
                else:
                    sous_resultat = sous_resultat.setdefault(cle, {})
                    sous_dictionnaire = sous_dictionnaire[cle]
            elif isinstance(sous_dictionnaire, list):
                sous_resultat = []
                for item in sous_dictionnaire:
                    sous_resultat.append(filtrer_attributs_par_chemin(item, [chemin[i:]], key, token))
                resultat[chemin[0]] = sous_resultat
                break

    # print(f"Résultat du filtrage des attributs par chemin: {resultat}")  # Log pour debug
    return transformer_json_entree(resultat)


def getAll_card(key, token):
    """
    Récupère toutes les cartes des listes spécifiées.
    """
    idList = ["671f465317b79fd50be2e628", "671f4658ef3675b58116fba2", "671f465d5576a36e7be95181"]
    allCard = []
    for i in idList:
        get_cards = get_cards_from_lists(i, key, token)
        # print(f"Cartes récupérées de la liste {i}: {get_cards}")  # Log pour debug
        for card in get_cards:
            card_filter = filtrer_attributs_par_chemin(card, chemins_a_garder, key, token)
            # print(f"Carte après filtrage: {card_filter}")  # Log pour debug
            allCard.append(card_filter)
    # print(f"Toutes les cartes récupérées après traitement: {allCard}")  # Log pour debug
    return allCard


def filtrer_json(json_data, attribut, valeur_filtre=None, jours_limite=None):
    """
    Filtre une liste de dictionnaires JSON en fonction d'un attribut spécifique ou des cartes dont la date d'échéance est
    dans moins de `jours_limite` jours.

    :param json_data: Liste de dictionnaires JSON (les cartes).
    :param attribut: L'attribut sur lequel filtrer.
    :param valeur_filtre: La valeur de l'attribut à filtrer.
    :param jours_limite: Si fourni, filtre les cartes dont la date d'échéance est supérieure à maintenant et inférieure à `jours_limite` jours.
    :return: Liste de cartes filtrées.
    """
    if attribut == "card_members_names":
        return [
            item
            for item in json_data
            if any(
                difflib.SequenceMatcher(None, member.lower(), valeur_filtre.lower()).ratio() > 0.7
                for member in item.get(attribut, [])
            )
        ]
    elif attribut == "due_date" and jours_limite is not None:
        maintenant = datetime.now()
        limite = maintenant + timedelta(days=jours_limite)
        return [
            item
            for item in json_data
            if "card_due_date" in item
            and maintenant < datetime.fromisoformat(item["card_due_date"].replace("Z", "")) <= limite
        ]
    else:
        return [item for item in json_data if item.get(attribut) == valeur_filtre]


def insert_into_db(cards, db_name="trello_cards.db"):
    """
    Insère les résultats dans une base de données SQLite.

    :param cards: Liste de dictionnaires JSON (les cartes).
    :param db_name: Nom de la base de données SQLite.
    """
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()

    # Création de la table si elle n'existe pas déjà
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_name TEXT,
            card_members_names TEXT,
            card_idLabels TEXT,
            card_desc TEXT,
            card_due_date TEXT,
            card_list_name TEXT,
            card_label_name TEXT
        )
    """)

    # Insertion des cartes
    for card in cards:
        cursor.execute(
            """
            INSERT INTO cards (card_name, card_members_names, card_idLabels, card_desc, card_due_date, card_list_name, card_label_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                card.get("card_name"),
                json.dumps(card.get("card_members_names", [])),  # Convertit la liste en chaîne JSON
                json.dumps(card.get("card_idLabels", [])),
                card.get("card_desc"),
                card.get("card_due_date"),
                card.get("card_list_name"),
                card.get("card_label_name"),
            ),
        )

    # Sauvegarde des changements et fermeture de la connexion
    connection.commit()
    connection.close()


def read_from_db(db_name="trello_cards.db", attribut=None, valeur_filtre=None):
    """
    Lit les cartes stockées dans la base de données SQLite avec des options de filtrage.

    :param db_name: Nom de la base de données SQLite.
    :param attribut: L'attribut sur lequel filtrer (par exemple, 'card_label_name').
    :param valeur_filtre: La valeur de l'attribut à filtrer.
    :return: Liste des cartes sous forme de dictionnaires.
    """
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()

    query = "SELECT card_name, card_members_names, card_idLabels, card_desc, card_due_date, card_list_name, card_label_name FROM cards"
    params = ()

    if attribut and valeur_filtre:
        query += f" WHERE {attribut} = ?"
        params = (valeur_filtre,)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    cards = []
    for row in rows:
        cards.append(
            {
                "card_name": row[0],
                "card_members_names": json.loads(row[1]),
                "card_idLabels": json.loads(row[2]),
                "card_desc": row[3],
                "card_due_date": row[4],
                "card_list_name": row[5],
                "card_label_name": row[6],
            }
        )

    connection.close()
    return cards


def get_trello_agent(
    model_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = False,
) -> Agent:
    return Agent(
        name="Trello Agent",
        agent_id="trello-agent",
        session_id=session_id,
        user_id=user_id,
        # The model to use for the agent
        model=OpenAIChat(
            id=model_id or agent_settings.gpt_4,
            max_tokens=agent_settings.default_max_completion_tokens,
            temperature=agent_settings.default_temperature,
        ),
        response_model=trello_card,
        structured_outputs=True,
        # model=Ollama(id="qwen2.5m:latest"),
        # Tools available to the agent
        tools=[create_card],
        # A description of the agent that guides its overall behavior
        role="Tu es un agent d'une Team qui dispose des capacités à interagir avec Trello. Tu es sollicité paar Agent Leader avec une demande précise. Tu dois renvoyer tes résultats à Agent Leader",
        # A list of instructions to follow, each as a separate item in the list
        instructions=[
            "Si l'utilisateur souhaite créer une nouvelle carte Trello : Utilise la structure de la classe trello_card pour renseigner les informations nécessaires. Une fois l'ensemble des informations collectées alors utilise la fonction create_card pour créer la carte.\n",
            "Tu peux donner cet exemple de carte Trello et expliquer les valeurs que peuvents prendre chaque attribut obligtoire.\n",
            "Voici la liste des champs obligatoire pour créer une crate Trello : \n",
            "    - card_name: Nom du chantier associé à la carte.\n",
            "    - card_label_name: Nom de la societe qui gère les actions à réaliser pour la carte.\n",
            "    - card_list_name: Nom de la liste dans laquelle la crate doit etre déposée.\n",
            "    - card_due_date: Date d'échéance de la carte..\n",
            "    - card_desc: Description de la carte.\n",
        ],
        # Format responses as markdown
        markdown=True,
        # Show tool calls in the response
        show_tool_calls=True,
        # Add the current date and time to the instructions
        add_datetime_to_instructions=True,
        # Store agent sessions in the database
        # storage=trello_agent_storage,
        # Enable read the chat history from the database
        # read_chat_history=True,
        # Store knowledge in a vector database
        # knowledge=lightRAG_agent_knowledge,
        # Enable searching the knowledge base
        # search_knowledge=True,
        # Enable monitoring on phidata.app
        monitoring=True,
        # Show debug logs
        debug_mode=True,
    )
