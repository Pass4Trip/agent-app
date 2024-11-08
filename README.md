## Spécifique Vinh-thuy
Je ne sais pas pourquoi les lib ne sont pas synchronisé entre mon local et les lib du docker

Ma solution est de m'assurer d'avoir en local :
- un pyproject.toml à jour avec l'ajout des lib nécessaire via : uv add XXXXX
- une regeneration du requirement.txt à partir du pyproject.toml via : scripts/generate_requirements.sh
- une installation du requirement.txt via : generate_requirements.sh : scripts/install.sh

Sur le container je lance un pip install e .  


Attention la lib transcription.py je la pose directmement sous app/app. 
  
OK
