#!/bin/bash

# Configuration
VPS_HOST="vps-af24e24d.vps.ovh.net"
VPS_IP="51.77.200.196"
VPS_USER="ubuntu"
REGISTRY_PORT="32000"
LOCAL_PATH="/Users/vinh/Documents/agent-app"

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🚀 Déploiement de l'API...${NC}"

# Build de l'image pour linux/amd64
echo -e "${YELLOW}🔨 Build de l'image Docker...${NC}"
docker build --platform linux/amd64 -t agent-api ${LOCAL_PATH}

# Tag de l'image pour le registry local
echo -e "${YELLOW}🏷️  Tag de l'image...${NC}"
docker tag agent-api ${VPS_IP}:${REGISTRY_PORT}/agent-api

# Push de l'image vers le registry
echo -e "${YELLOW}📤 Push de l'image vers le registry...${NC}"
docker push ${VPS_IP}:${REGISTRY_PORT}/agent-api

# Redéploiement du pod api
echo -e "${YELLOW}🔄 Redéploiement de l'API...${NC}"
if ssh ${VPS_USER}@${VPS_HOST} "microk8s kubectl rollout restart deployment agent-api && \
    microk8s kubectl rollout status deployment agent-api"; then
    
    # Vérification détaillée du pod
    echo -e "${YELLOW}🔍 Vérification du pod déployé...${NC}"
    
    # Récupérer les détails du pod
    POD_INFO=$(ssh ${VPS_USER}@${VPS_HOST} "microk8s kubectl get pods -l app=agent-api -o=jsonpath='{.items[0].metadata.name} {.items[0].status.containerStatuses[0].imageID} {.items[0].status.containerStatuses[0].image} {.items[0].metadata.creationTimestamp}'")
    
    echo -e "${YELLOW}Détails du pod :${NC}"
    echo "$POD_INFO" | awk '{print "Nom du pod: " $1 "\nImage ID: " $2 "\nImage: " $3 "\nDate de création: " $4}'
    
    # Si le déploiement est réussi, commit et push
    echo -e "${YELLOW}📦 Sauvegarde des changements sur Git...${NC}"
    read -p "Message de commit: " COMMIT_MSG
    if [ ! -z "$COMMIT_MSG" ]; then
        git add .
        git commit -m "$COMMIT_MSG"
        
        # Vérification du statut Git avant push
        echo -e "${YELLOW}🔍 Vérification du statut Git...${NC}"
        git status
        
        # Push avec affichage détaillé
        echo -e "${YELLOW}📤 Envoi sur GitHub...${NC}"
        git push -v origin feature/clean-start
        
        echo -e "${GREEN}✅ Changements sauvegardés sur Git${NC}"
    else
        echo -e "${YELLOW}⚠️  Pas de commit Git (message vide)${NC}"
    fi
    
    # Vérifier la version déployée avec plus de détails
    echo -e "${YELLOW}📋 Logs du pod :${NC}"
    ssh ${VPS_USER}@${VPS_HOST} "microk8s kubectl logs deployment/agent-api --tail=20"
    
    echo -e "${GREEN}✅ Déploiement terminé avec succès${NC}"
else
    echo -e "${RED}❌ Échec du déploiement${NC}"
    exit 1
fi
