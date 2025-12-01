import json
from random import choice

def getQuestion():
    with open('quiz/xmas.json', 'r') as f:
        questions = json.load(f)
    return choice(questions)