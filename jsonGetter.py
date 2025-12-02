import json
from random import choice

def getQuestion():
    with open('resources/quiz/xmas.json', 'r') as f:
        questions = json.load(f)
    return choice(questions)

def getCharade():
    with open('resources/charades/xmas.json', 'r') as f:
        charades = json.load(f).get("charades", [])
    return choice(charades)