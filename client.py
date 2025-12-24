import tkinter as tk
from tkinter import ttk
import websockets
import json
import threading
import asyncio
import queue

CLIENT_VERSION = "BETA 0.1"

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

                if cmd is not None:
                    print(f"Sending command to server: {cmd}")
                    await websocket.send(json.dumps(cmd))
                
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    incomingMessages.put(json.loads(message))
                except asyncio.TimeoutError:
                    pass
        
                await asyncio.sleep(0.01)
    
    asyncio.run(handler())


class Window:
    def __init__(self):
        self.__window = tk.Tk()
        self.__window.geometry("800x800")
        self.__window.resizable(False,False)
        self.__window.title(f"XMAS GAME Client - Running version v{CLIENT_VERSION}")
        
        # Configure button styles for larger text
        style = ttk.Style()
        style.configure('Large.TButton', font=('Segoe UI', 16))
    
    def getWindow(self):
        return self.__window


class LobbyScreen:
    def __init__(self, menuWindow):
        self.__window = menuWindow
        self.__title = Title(self.__window.getWindow())

        self.__lobbyCodeLabel = ttk.Label(self.__window.getWindow(), text="Lobby Code:", font=("Segoe UI", 20))
        self.__lobbyCodeLabel.pack(pady=10)
        self.__lobbyCodeEntry = ttk.Entry(self.__window.getWindow(), font=("Segoe UI", 20))
        self.__lobbyCodeEntry.pack(pady=10)

        self.__teamNameLabel = ttk.Label(self.__window.getWindow(), text="Team Name:", font=("Segoe UI", 20))
        self.__teamNameLabel.pack(pady=10)
        self.__teamNameEntry = ttk.Entry(self.__window.getWindow(), font=("Segoe UI", 20))
        self.__teamNameEntry.pack(pady=10)

        self.__serverLabel = ttk.Label(self.__window.getWindow(), text=f"Server:", font=("Segoe UI", 16))
        self.__serverLabel.pack(pady=10)
        self.__serverEntry = ttk.Entry(self.__window.getWindow(), font=("Segoe UI", 16))
        self.__serverEntry.insert(0, "localhost:8000")
        self.__serverEntry.pack(pady=5)

        self.__joinLobbyButton = ttk.Button(self.__window.getWindow(), text="Join Lobby", command=lambda: self.joinLobby(self.__serverEntry.get()), style="Large.TButton")
        self.__joinLobbyButton.pack(pady=20)

        self.__startButton = ttk.Button(self.__window.getWindow(), text="Start Game", command=self.startGame, state="disabled", style="Large.TButton")
        self.__startButton.pack(pady=20)

        self.__teamsFrame = ttk.Frame(self.__window.getWindow())
        self.__teamsFrame.pack(pady=20)
        self.__teamsLabel = ttk.Label(self.__teamsFrame, text="Teams in Lobby:", font=("Segoe UI", 16))
        self.__teamsLabel.pack(pady=10)

    def startGame(self):
        outgoingCommands.put({"command": "start"})
        

    def getWindow(self):
        return self.__window.getWindow()
    
    def joinLobby(self, server):
        lobbyCode = self.__lobbyCodeEntry.get()
        teamName = self.__teamNameEntry.get()

        self.__lobbyCodeEntry.config(state="disabled") # disable entries to prevent changes after joining
        self.__teamNameEntry.config(state="disabled")
        self.__joinLobbyButton.config(state="disabled")

        print(f"Joining lobby {lobbyCode} as {teamName} on server {server}")

        # start websocket thread
        uri = f"ws://{server}/ws/{lobbyCode}/{teamName}"
        wsThread = threading.Thread(target=websocketHandlerThread, args=(uri,), daemon=True)
        wsThread.start()
        self.pollIncomingMessages()

    def pollIncomingMessages(self):
        try:
            while True:
                message = incomingMessages.get_nowait()
                print(f"Received message from server: {message}")

                if "status" in message:
                    status = message["status"]
                    if status == "lobbyJoined":
                        print(f"Successfully joined lobby {message['lobbyCode']} as {message['clientID']}")
                        if message["isHost"] == True:
                            self.__startButton.config(state="normal")

                    elif status == "error":
                        print(f"Error from server: {message['errorMessage']}")

                    elif status == "start":
                        print("Game starting!")
                        self.__window.getWindow().destroy()
                        self.__gameScreen = GameScreen(Window())
                        
                    elif status == "teamUpdate":
                        self.__teamsFrame.destroy()
                        self.__teamsFrame = ttk.Frame(self.__window.getWindow())
                        self.__teamsFrame.pack(pady=20)
                        self.__teamsLabel = ttk.Label(self.__teamsFrame, text="Teams in Lobby:", font=("Segoe UI", 20))
                        self.__teamsLabel.pack(pady=10)

                        teamNames = message["teamNames"]
                        for teamName in teamNames:
                            teamLabel = ttk.Label(self.__teamsFrame, text=teamName, font=("Segoe UI", 18))
                            teamLabel.pack(pady=5)
                

        except queue.Empty:
            pass
            
        self.__window.getWindow().after(100, self.pollIncomingMessages)


class GameScreen:
    def __init__(self, gameWindow):
        self.__window = gameWindow
        self.__score = 0 # score is kept track of both client and server side because it can then be displayed instantly without waiting for server response
        self.__title = Title(self.__window.getWindow())
        self.__resultLabel = None

        self.__scoreLabel = ttk.Label(self.__window.getWindow(), text=f"Score: {self.__score}", font=("Segoe UI", 20))
        self.__scoreLabel.pack(pady=10)
    
        self.__gameFrame = ttk.Frame(self.__window.getWindow())
        self.__gameFrame.pack()

        print("Requesting question from server")
        self.requestNewTask()

        print("Starting polling")
        self.pollIncomingMessages()

    def getWindow(self):
        return self.__window.getWindow()

    def quiz(self, question, options, answer):
        print("Entering quiz")
        qLabel = ttk.Label(self.__gameFrame, text=question, font=("Segoe UI", 24), wraplength=600, justify="center")
        qLabel.pack(pady=20)

        self.__buttonsGrid = ttk.Frame(self.__gameFrame)
        self.__buttonsGrid.pack()
        
        rowCounter = 0
        colCounter = 0
        quizButtons = []

        for option, text in options.items():
            oButton = ttk.Button(self.__buttonsGrid, text=text, command=lambda opt=option, buttons=quizButtons: self.checkQuizAnswer(opt, answer, buttons), style="Large.TButton")
            quizButtons.append(oButton)
            oButton.grid(row=rowCounter, column=colCounter, padx=10, pady=10)
            colCounter += 1
            if colCounter > 1:
                colCounter = 0
                rowCounter += 1

    def reset(self):
        self.__gameFrame.destroy()
        self.__gameFrame = ttk.Frame(self.__window.getWindow())
        self.__gameFrame.pack()
        
        self.requestNewTask()
        self.pollIncomingMessages()


    def checkQuizAnswer(self, selected, correct, buttons):
        # Disable all quiz buttons to prevent multiple answers
        for button in buttons:
            button.config(state="disabled")
            
        if selected == correct:
            result = "Correct!"
            self.updateScore(1)
        else:
            result = f"Wrong! The correct answer was {correct}."
        self.__window.getWindow().after(2000, self.reset)
        self.__resultLabel = ttk.Label(self.__gameFrame, text=result, font=("Segoe UI", 20))
        self.__resultLabel.pack(pady=20)

    
    def updateScore(self, points):
        outgoingCommands.put({"command": "addPoints", "points": points})
        self.__score += points
        self.__scoreLabel.config(text=f"Score: {self.__score}")
    
    def charades(self, charade):
        titleLabel = ttk.Label(self.__gameFrame, text="Charades", font=("Segoe UI", 24))
        titleLabel.pack(pady=20)

        turnScreenLabel = ttk.Label(self.__gameFrame, text="Turn the screen so only one player can see it!", font=("Segoe UI", 18))
        turnScreenLabel.pack(pady=10)

        revealButton = ttk.Button(self.__gameFrame, text="Reveal Charade", command=lambda: self.revealCharade(revealButton, charade), style="Large.TButton")
        revealButton.pack(pady=10)

    def revealCharade(self, button, charade):
        button.config(state="disabled")
        charadeLabel = ttk.Label(self.__gameFrame, text=charade, font=("Segoe UI", 20))
        charadeLabel.pack(pady=20)

        correctButton = ttk.Button(self.__gameFrame, text="Correct", command=lambda: self.charadesAnswerPressed(True, correctButton, wrongButton), style="Large.TButton")
        correctButton.pack(pady=10) 

        wrongButton = ttk.Button(self.__gameFrame, text="Wrong", command=lambda: self.charadesAnswerPressed(False, correctButton, wrongButton), style="Large.TButton")
        wrongButton.pack(pady=10)

    def charadesAnswerPressed(self, correct, correctButton, wrongButton):
        correctButton.config(state="disabled")
        wrongButton.config(state="disabled")
        
        if correct:
            self.updateScore(1)
            self.__resultLabel = ttk.Label(self.__gameFrame, text="Correct!", font=("Segoe UI", 20))
        else:
            self.__resultLabel = ttk.Label(self.__gameFrame, text="Wrong!", font=("Segoe UI", 20))
        self.__resultLabel.pack(pady=20)
        self.__window.getWindow().after(2000, self.reset)


    def whoAmI(self, whoami):
        titleLabel = ttk.Label(self.__gameFrame, text="Who Am I?", font=("Segoe UI", 24))
        titleLabel.pack(pady=20)

        promptLabel = ttk.Label(self.__gameFrame, text=f"{whoami["question"]}", font=("Segoe UI", 20), wraplength=600, justify="center")
        promptLabel.pack(pady=20)

        whoAmIButtons = []
        for x in range(len(whoami["options"])):
            option = whoami["options"][x]
            oButton = ttk.Button(self.__gameFrame, text=option, command=lambda opt=option, buttons=whoAmIButtons: self.checkWhoAmIAnswer(opt, whoami["answer"], buttons), style="Large.TButton") # opt=option to bind current value
            whoAmIButtons.append(oButton)
            oButton.pack(pady=10)

    def checkWhoAmIAnswer(self, selected, correct, buttons): # selected option and correct answer and buttons to be disabled
        for button in buttons:
            button.config(state="disabled")
            
        if selected == correct:
            result = "Correct!"
            self.updateScore(1)
        else:
            result = f"Wrong! The correct answer was {correct}."
        self.__window.getWindow().after(1500, self.reset)
        self.__resultLabel = ttk.Label(self.__gameFrame, text=result, font=("Segoe UI", 20))
        self.__resultLabel.pack(pady=20)

    
    def requestNewTask(self):
        outgoingCommands.put({"command": "newTask"})
        print(f"Queue size after request: {outgoingCommands.qsize()}")

    def pollIncomingMessages(self):
        try:
            while True:
                message = incomingMessages.get_nowait()
                print(f"Received message from server: {message}")
                if "type" in message and "task" in message:
                    gamemode = message["type"]
                    task = message["task"]
                    if gamemode == "quiz":
                        questionData = task
                        questionText = questionData["question"]
                        options = questionData["options"]
                        answer = questionData["answer"]
                        self.quiz(questionText, options, answer)

                    elif gamemode == "charades":
                        self.charades(task)
                    elif gamemode == "whoami":
                        self.whoAmI(task)
                
                elif "status" in message:
                    status = message["status"]
                    if status == "roundEnded":
                        self.__gameFrame.destroy()
                        self.__gameFrame = ttk.Frame(self.__window.getWindow())
                        self.__gameFrame.pack()
                        roundEndLabel = ttk.Label(self.__gameFrame, text="Round Ended!", font=("Segoe UI", 24))
                        roundEndLabel.pack(pady=20)
                        # reset and restart timer after 2 minutes
                        self.__window.getWindow().after(120000, self.reset)
                
                    elif status == "gameEnded":
                        self.__gameFrame.destroy()
                        self.__gameFrame = ttk.Frame(self.__window.getWindow())
                        self.__gameFrame.pack()
                        gameEndLabel = ttk.Label(self.__gameFrame, text="Game Ended!", font=("Segoe UI", 24))
                        gameEndLabel.pack(pady=20)
                        # request scores
                        outgoingCommands.put({"command": "requestScores"})

                elif "scores" in message:
                    scores = message["scores"]
                    scoresText = "Final Scores:\n"
                    for team, score in scores.items():
                        scoresText += f"{team}: {score}\n"
                    scoresLabel = ttk.Label(self.__gameFrame, text=scoresText, font=("Segoe UI", 20))
                    scoresLabel.pack(pady=20)
                
        except queue.Empty:
            pass
            
        self.__window.getWindow().after(100, self.pollIncomingMessages)



class Title:
    def __init__(self, parent):
        self.__frame = ttk.Frame(parent)
        self.__frame.pack()
        self.__text = ttk.Label(self.__frame, text="Lukey's Quiz Game", font=("Segoe UI", 42, "bold"))
        self.__text.pack()


if __name__ == "__main__":    
    screen = LobbyScreen(Window())
    screen.getWindow().mainloop()