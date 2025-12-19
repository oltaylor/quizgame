import tkinter as tk
from tkinter import ttk
import random
import jsonGetter
import websockets
import json
import threading
import asyncio
import queue

CLIENT_VERSION = "PRE-ALPHA"
SERVER = "localhost:8000"

outgoingCommands = queue.Queue() # bridge between websocket thread and main thread
incomingMessages = queue.Queue() # messages from server to main thread

def websocketHandlerThread(uri):
    async def handler():
        async with websockets.connect(uri) as websocket:
            while True:
                try:
                    cmd = outgoingCommands.get_nowait()
                except queue.Empty:
                    cmd = None

                if cmd:
                    await websocket.send(json.dumps(cmd))
                
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    incomingMessages.put(json.loads(message))
                except asyncio.TimeoutError:
                    pass
    
    asyncio.run(handler())



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
        self.__availableGames = ["quiz", "charades", "whoami"]
        self.__window = gameWindow
        self.__score = 0 # To be replaced with API
        self.__title = Title(self.__window.getWindow())
        #self.__activeGame = "quiz" # pick game, eventually from server
        self.__resultLabel = None

        self.__scoreLabel = ttk.Label(self.__window.getWindow(), text=f"Score: {self.__score}", font=("Segoe UI", 16))
        self.__scoreLabel.pack(pady=10)
    
        self.__gameFrame = ttk.Frame(self.__window.getWindow())
        self.__gameFrame.pack()

        #if self.__activeGame == "quiz":
        #    self.quiz()
        #elif self.__activeGame == "charades":
        #    self.charades()
        #elif self.__activeGame == "whoami":
        #    self.whoAmI()

        self.pollIncomingMessages()

    def getWindow(self):
        return self.__window.getWindow()
    
    def getGame(self):
        return random.choice(self.__availableGames)

    def quiz(self, question, options):
        print("Entering quiz")
        qLabel = ttk.Label(self.__gameFrame, text=question, font=("Segoe UI", 20), wraplength=600, justify="center")
        qLabel.pack(pady=20)
        for option, text in options.items():
            oButton = ttk.Button(self.__gameFrame, text=text, command=lambda opt=option: self.checkQuizAnswer(opt, question['answer']))
            oButton.pack(pady=10)

    def requestQuestionFromServer(self):
        outgoingCommands.put({"command": "newQuizQuestion"})
        while True:
            try:
                message = incomingMessages.get_nowait()
                if message.get("question"):
                    return message["question"]
            except queue.Empty:
                pass

    def pollIncomingMessages(self):
        while incomingMessages.empty():
            print("polling")
            message = incomingMessages.get()
            
            if message.get("question"):
                self.quiz(message["question"], message["options"])
            
        self.__window.getWindow().after(100, self.pollIncomingMessages)

    def reset(self):
        self.__gameFrame.destroy()
        self.__gameFrame = ttk.Frame(self.__window.getWindow())
        self.__gameFrame.pack()
        
        self.__activeGame = self.getGame()
        #if self.__activeGame == "quiz":
        #    self.quiz()
        #elif self.__activeGame == "charades":
        #    self.charades()
        #elif self.__activeGame == "whoami":
        #    self.whoAmI()

    def checkQuizAnswer(self, selected, correct):
        if selected == correct:
            result = "Correct!"
            self.updateScore(1)
            self.__window.getWindow().after(2000, self.reset)
        else:
            result = f"Wrong! The correct answer was {correct}."
        self.__resultLabel = ttk.Label(self.__gameFrame, text=result, font=("Segoe UI", 16))
        self.__resultLabel.pack(pady=20)

    
    def updateScore(self, points):
        self.__score += points
        self.__scoreLabel.config(text=f"Score: {self.__score}")
    
    def charades(self):
        titleLabel = ttk.Label(self.__gameFrame, text="Charades", font=("Segoe UI", 20))
        titleLabel.pack(pady=20)

        turnScreenLabel = ttk.Label(self.__gameFrame, text="Turn the screen so only one player can see it!", font=("Segoe UI", 14))
        turnScreenLabel.pack(pady=10)

        revealButton = ttk.Button(self.__gameFrame, text="Reveal Charade", command=lambda: self.revealCharade(revealButton))
        revealButton.pack(pady=10)

    def revealCharade(self, button):
        button.config(state="disabled")
        charade = jsonGetter.getCharade()
        charadeLabel = ttk.Label(self.__gameFrame, text=charade, font=("Segoe UI", 16))
        charadeLabel.pack(pady=20)

        correctButton = ttk.Button(self.__gameFrame, text="Correct", command=lambda: self.charadesAnswerPressed(True))
        correctButton.pack(pady=10) 

        wrongButton = ttk.Button(self.__gameFrame, text="Wrong", command=lambda: self.charadesAnswerPressed(False))
        wrongButton.pack(pady=10)

    def charadesAnswerPressed(self, correct):
        if correct:
            self.updateScore(1)
            self.__resultLabel = ttk.Label(self.__gameFrame, text="Correct!", font=("Segoe UI", 16))
        else:
            self.__resultLabel = ttk.Label(self.__gameFrame, text="Wrong!", font=("Segoe UI", 16))
        self.__window.getWindow().after(2000, self.reset)


    def whoAmI(self):
        titleLabel = ttk.Label(self.__gameFrame, text="Who Am I?", font=("Segoe UI", 20))
        titleLabel.pack(pady=20)

        whoami = jsonGetter.getWhoAmI()
        promptLabel = ttk.Label(self.__gameFrame, text=f"{whoami["question"]}", font=("Segoe UI", 16), wraplength=600, justify="center")
        promptLabel.pack(pady=20)

        # display option buttons
        for x in range(len(whoami["options"])):
            option = whoami["options"][x]
            oButton = ttk.Button(self.__gameFrame, text=option, command=lambda opt=option: self.checkWhoAmIAnswer(opt, whoami["answer"])) # opt=option to bind current value
            oButton.pack(pady=10)

    def checkWhoAmIAnswer(self, selected, correct): # selected option and correct answer
        if selected == correct:
            result = "Correct!"
            self.updateScore(1)
            self.__window.getWindow().after(2000, self.reset)
        else:
            result = f"Wrong! The correct answer was {correct}."
        self.__resultLabel = ttk.Label(self.__gameFrame, text=result, font=("Segoe UI", 16))
        self.__resultLabel.pack(pady=20)



class Title:
    def __init__(self, parent):
        self.__frame = ttk.Frame(parent)
        self.__frame.pack()
        self.__text = ttk.Label(self.__frame, text="GAME", font=("Segoe UI", 35, "bold"))
        self.__text.pack()


if __name__ == "__main__":
    screen = LobbyScreen(Window())
    screen.getWindow().mainloop()

    threading.Thread(target=websocketHandlerThread, args=(f"ws://{SERVER}/ws/TEST/Client1",)).start()