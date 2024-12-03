# Guide de Déploiement - Agent App

Ce guide détaille les étapes pour déployer et mettre à jour l'application sur le VPS OVH.

## 1. Construction et Push des Images Docker

Après modification du code sur votre Mac, reconstruire et pousser les images :

### Pour agent-app
```bash
# Sur votre Mac
cd /Users/vinh/Documents/agent-app
docker build --platform linux/amd64 -t agent-app .
docker tag agent-app 51.77.200.196:32000/agent-app
docker push 51.77.200.196:32000/agent-app
```

### Pour agent-api
```bash
# Sur votre Mac
cd /Users/vinh/Documents/agent-app
docker build --platform linux/amd64 -t agent-api .
docker tag agent-api 51.77.200.196:32000/agent-api
docker push 51.77.200.196:32000/agent-api
```

## 2. Mise à jour des Configurations Kubernetes

### Structure des fichiers YAML
Les fichiers de configuration se trouvent dans le dossier `/home/ubuntu/phidata_yaml/` sur le VPS :
- `secrets.yaml` : Variables d'environnement sensibles
- `db-deployment.yaml` : Déploiement PostgreSQL
- `api-deployment.yaml` : Déploiement FastAPI
- `app-deployment.yaml` : Déploiement Streamlit
- `ingress.yaml` : Configuration de l'accès externe
- `db-service.yaml` : Service NodePort pour accès PostgreSQL

### Après modification des fichiers YAML
```bash
# Depuis le dossier k8s sur votre Mac
scp *.yaml ubuntu@51.77.200.196:/home/ubuntu/phidata_yaml/

# Sur le VPS
cd /home/ubuntu/phidata_yaml/
microk8s kubectl apply -f secrets.yaml
microk8s kubectl apply -f db-deployment.yaml
microk8s kubectl apply -f db-service.yaml
microk8s kubectl apply -f api-deployment.yaml
microk8s kubectl apply -f app-deployment.yaml
microk8s kubectl apply -f ingress.yaml
```

## 3. Accès aux Services

### Application Web
- Interface Streamlit : http://vps-af24e24d.vps.ovh.net/
- API FastAPI : http://vps-af24e24d.vps.ovh.net/api/
- Documentation API (Swagger) : http://vps-af24e24d.vps.ovh.net/docs/
- OpenAPI JSON : http://vps-af24e24d.vps.ovh.net/openapi.json

### Base de Données PostgreSQL
Configuration DBeaver :
- Host: vps-af24e24d.vps.ovh.net
- Port: 30432
- Database: ai
- Username: ai
- Password: ai

## 4. Commandes Utiles

### Vérifier l'état des services
```bash
# État des pods
microk8s kubectl get pods

# État des services
microk8s kubectl get services

# État de l'ingress
microk8s kubectl get ingress
```

### Consulter les logs
```bash
# Logs de l'application Streamlit
microk8s kubectl logs -f deployment/agent-app

# Logs de l'API
microk8s kubectl logs -f deployment/agent-api

# Logs de la base de données
microk8s kubectl logs -f deployment/agent-db
```

### Redémarrer les services
```bash
# Redémarrer l'application Streamlit
microk8s kubectl rollout restart deployment agent-app

# Redémarrer l'API
microk8s kubectl rollout restart deployment agent-api

# Redémarrer la base de données
microk8s kubectl rollout restart deployment agent-db
```

## 5. Dépannage Courant

### Si un pod est en CrashLoopBackOff
```bash
# Vérifier les logs
microk8s kubectl logs <nom-du-pod>

# Supprimer et recréer le pod
microk8s kubectl delete pod <nom-du-pod>
```

### Pour le pod PostgreSQL
Si la base de données ne démarre pas à cause d'un répertoire non vide :
```bash
# Supprimer le PVC
microk8s kubectl delete pvc postgres-pv-claim
# Réappliquer le déploiement
microk8s kubectl apply -f db-deployment.yaml
```

### Pour accéder à un pod
```bash
microk8s kubectl exec -it <nom-du-pod> -- /bin/bash
```

## 6. Sécurité

### Base de données
Pour sécuriser l'accès à PostgreSQL, il est recommandé de :
1. Configurer un pare-feu pour limiter l'accès au port 30432
```bash
sudo ufw allow from <votre-ip> to any port 30432 proto tcp
```
2. Utiliser des mots de passe forts dans `secrets.yaml`
3. Configurer SSL pour les connexions PostgreSQL

## Variables d'Environnement
Configurées dans `secrets.yaml` :
- DB_USER: "ai"
- DB_PASSWORD: "ai"
- DB_DATABASE: "ai"
- OPENAI_API_KEY: [Votre clé API]
- PHI_API_KEY: [Votre clé API]

## Agent App

## Description
Ce projet est une application d'agent conversationnel qui permet d'interagir avec une API de chat via Python.

## Fichiers Principaux

### MyBoun_chat.py
Un script Python pour envoyer des messages à une API de chat et recevoir des réponses.

#### Fonctionnalités
- Envoi de messages à un agent conversationnel
- Support pour différents paramètres de configuration
- Gestion robuste des réponses de l'API

#### Utilisation
```bash
# Utilisation de base
python MyBoun_chat.py "Votre message ici"

# Avec des paramètres personnalisés
python MyBoun_chat.py "Bonjour" --agent_id mon_agent --session_id ma_session
```

#### Paramètres
- `message` : Le message à envoyer (obligatoire)
- `--agent_id` : ID de l'agent (défaut : "example-agent")
- `--session_id` : ID de session (défaut : "vinh_session_id")
- `--user_id` : ID utilisateur (défaut : "vinh_id")
- `--url` : URL de l'API de chat (défaut : "http://vps-af24e24d.vps.ovh.net/v1/playground/agent/run")

## Dépendances
- Python 3.x
- `requests` (pour les requêtes HTTP)

## Installation
1. Clonez le dépôt
2. Installez les dépendances :
```bash
pip install requests
```

## Contribution
N'hésitez pas à ouvrir des issues ou à soumettre des pull requests.

## Licence
[À spécifier]
