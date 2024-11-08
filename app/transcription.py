# voice_assistant/transcription.py

import json
import logging
import requests
import time

from colorama import Fore, init
from openai import OpenAI


fast_url = "http://host.docker.internal:5403"
checked_fastwhisperapi = False

# def transcribe_audio(audio_file_path):

#     endpoint = f"{fast_url}/v1/transcriptions"
#     #audio_file_path= "app/audio_file4.wav"

#     files = {'file': (audio_file_path, open(audio_file_path, 'rb'))}
#     data = {
#         'model': "base",
#         'language': "fr",
#         'initial_prompt': None,
#         'vad_filter': True,
#     }


#     response = requests.post(endpoint, files=files, data=data, headers=headers)
#     print(" !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
#     response_json = response.json()
#     print("response_json : ", response_json)
#     return response_json.get('text', 'No text found in the response.')


def transcribe_audio(audio_file_path):
    endpoint = f"{fast_url}/v1/"

    client = OpenAI(api_key="cant-be-empty", base_url=endpoint)

    audio_file = open(audio_file_path, "rb")

    transcript = client.audio.transcriptions.create(model="Systran/faster-whisper-tiny", file=audio_file)
    print(transcript.text)

    return transcript.text
