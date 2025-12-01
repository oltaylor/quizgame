import requests
import time
import tkinter as tk
from tkinter import ttk
import threading
import random
import quiz

CLIENT_VERSION = "PRE-ALPHA"
SERVER = "localhost:8000"

class Window:
    def __init__(self):
        self.__window = tk.Tk()
        self.__window.geometry("800x800")
        self.__window.resizable(False,False)
        self.__window.title(f"XMAS GAME Client - Running version v{CLIENT_VERSION}")
    
    def getWindow(self):
        return self.__window

class LobbyScreen:
    def __init__(self, menuWindow):
        self.__window = menuWindow
        self.__title = Title(self.__window.getWindow())

        self.__startButton = ttk.Button(self.__window.getWindow(), text="Start Game", command=self.startGame)
        self.__startButton.pack(pady=20)

    def startGame(self):
        self.__window.getWindow().destroy()
        self.__gameScreen = GameScreen(Window())

    
    def getWindow(self):
        return self.__window.getWindow()


class GameScreen:
    def __init__(self, gameWindow):
        self.__window = gameWindow
        self.__title = Title(self.__window.getWindow())
        self.__gameFrame = ttk.Frame(self.__window.getWindow())
        self.__gameFrame.pack()
        self.__activeGame = None
        self.quiz()
    
    def getWindow(self):
        return self.__window.getWindow()
    
    def getGame(self):
        # 1 - quiz
        # 2 - charades
        # 3 - who am i
        # 4 - pictionary?
        choice = random.randint(1,4)
        if self.__activeGame == 1:
            self.__activeGame = "quiz"
        elif self.__activeGame == 2:
            self.__activeGame = "charades"
        elif self.__activeGame == 3:
            self.__activeGame = "whoami"
        elif self.__activeGame == 4:
            self.__activeGame = "pictionary"
        return choice

    def quiz(self):
        question = quiz.getQuestion()
        qLabel = ttk.Label(self.__gameFrame, text=question['question'], font=("Segoe UI", 20))
        qLabel.pack(pady=20)
        for option, text in question['options'].items():
            oButton = ttk.Button(self.__gameFrame, text=text, command=lambda opt=option: self.checkAnswer(opt, question['answer']))
            oButton.pack(pady=10)

    def quizReset(self):
        self.__gameFrame.destroy()
        self.__gameFrame = ttk.Frame(self.__window.getWindow())
        self.quiz()

    
    def checkAnswer(self, selected, correct):
        if selected == correct:
            result = "Correct!"
            self.__window.getWindow().after(2000, self.quizReset)
        else:
            result = f"Wrong! The correct answer was {correct}."
        resultLabel = ttk.Label(self.__window.getWindow(), text=result, font=("Segoe UI", 16))
        resultLabel.pack(pady=20)
        

class Title:
    def __init__(self, parent):
        self.__frame = ttk.Frame(parent)
        self.__frame.pack()
        self.__text = ttk.Label(self.__frame, text="GAME", font=("Segoe UI", 35, "bold"))
        self.__text.pack()


if __name__ == "__main__":
    screen = LobbyScreen(Window())
    screen.getWindow().mainloop()