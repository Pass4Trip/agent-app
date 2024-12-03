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
    
    # Si le déploiement est réussi, commit et push
    echo -e "${YELLOW}📦 Sauvegarde des changements sur Git...${NC}"
    read -p "Message de commit: " COMMIT_MSG
    if [ ! -z "$COMMIT_MSG" ]; then
        git add .
        git commit -m "$COMMIT_MSG"
        git push
        echo -e "${GREEN}✅ Changements sauvegardés sur Git${NC}"
    else
        echo -e "${YELLOW}⚠️  Pas de commit Git (message vide)${NC}"
    fi
    
    # Vérifier la version déployée
    echo -e "${YELLOW}📋 Vérification de la version déployée...${NC}"
    sleep 5  # Attendre que le pod soit prêt
    ssh ${VPS_USER}@${VPS_HOST} "microk8s kubectl logs -f deployment/agent-api --tail=20 | grep 'Initializing Example Agent'"
    
    echo -e "${GREEN}✅ Déploiement terminé avec succès${NC}"
else
    echo -e "${RED}❌ Échec du déploiement${NC}"
    exit 1
fi
