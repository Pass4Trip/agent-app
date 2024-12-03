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

# Nettoyer les images locales
echo -e "${YELLOW}🧹 Nettoyage des images locales...${NC}"
docker rmi -f agent-api ${VPS_IP}:${REGISTRY_PORT}/agent-api 2>/dev/null || true

# Build de l'image pour linux/amd64
echo -e "${YELLOW}🔨 Build de l'image Docker...${NC}"
docker build --no-cache --platform linux/amd64 -t agent-api ${LOCAL_PATH}

# Tag de l'image pour le registry local
echo -e "${YELLOW}🏷️  Tag de l'image...${NC}"
docker tag agent-api ${VPS_IP}:${REGISTRY_PORT}/agent-api

# Push de l'image vers le registry
echo -e "${YELLOW}📤 Push de l'image vers le registry...${NC}"
docker push ${VPS_IP}:${REGISTRY_PORT}/agent-api

# Nettoyer et préparer le VPS
echo -e "${YELLOW}🧹 Préparation du VPS...${NC}"
ssh -v ${VPS_USER}@${VPS_HOST} "
    set -x  # Mode debug pour afficher chaque commande
    
    echo '🔍 Vérification des images existantes'
    microk8s ctr image ls | grep ${VPS_IP}:${REGISTRY_PORT}/agent-api || echo 'Aucune image trouvée'
    
    echo '🗑️ Tentative de suppression des anciennes images'
    microk8s ctr image rm ${VPS_IP}:${REGISTRY_PORT}/agent-api 2>&1 || echo 'Aucune image à supprimer'
    
    echo '📥 Vérification de la connectivité docker'
    docker info 2>&1
    
    echo '📦 Tentative de pull de l\'image'
    docker pull ${VPS_IP}:${REGISTRY_PORT}/agent-api 2>&1
    PULL_STATUS=$?
    
    echo '🔬 Statut du pull : $PULL_STATUS'
    if [ $PULL_STATUS -eq 0 ]; then
        echo '🚢 Import de l\'image dans microk8s'
        docker save ${VPS_IP}:${REGISTRY_PORT}/agent-api | microk8s ctr image import - 2>&1
        IMPORT_STATUS=$?
        echo '🔬 Statut de l\'import : $IMPORT_STATUS'
        
        echo '📋 Vérification des images importées'
        microk8s ctr image ls | grep ${VPS_IP}:${REGISTRY_PORT}/agent-api
    else
        echo '❌ Échec du pull de l\'image'
        exit 1
    fi
" 2>&1 | tee /tmp/vps_deploy.log

# Redéploiement du pod api
echo -e "${YELLOW}🔄 Redéploiement de l'API...${NC}"
if ssh ${VPS_USER}@${VPS_HOST} "
    # Forcer le redéploiement
    microk8s kubectl rollout restart deployment agent-api
    microk8s kubectl rollout status deployment agent-api
"; then
    
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
