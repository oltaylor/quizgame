import requests
import time
import tkinter as tk
from tkinter import ttk
import threading

CLIENT_VERSION = "PRE-ALPHA"
SERVER = "localhost:8000"

class Window:
    def __init__(self):
        self.__window = tk.Tk()
        self.__window.geometry("800x800")
        self.__window.resizable(False,False)
        self.__window.title(f"Charades Client - Running version v{CLIENT_VERSION}")
    
    def getWindow(self):
        return self.__window
    

class LobbyScreen:
    def __init__(self, menuWindow):
        self.__window = menuWindow
        self.__lobbyCode = None
        self.__title = Title(self.__window.getWindow())
        self.__lobbyJoining = LobbyJoining(self.__window.getWindow(), self.setLobbyCode)
    
    def getWindow(self):
        return self.__window.getWindow()
    
    def getLobbyCode(self):
        return self.__lobbyCode

    def setHost(self):
        self.__host = True

    def setLobbyCode(self, lobbyCode):
        self.__lobbyCode = lobbyCode
        self.__hostOpts = HostOptions(self.__window.getWindow(), self.__lobbyCode)


class Title:
    def __init__(self, parent):
        self.__frame = ttk.Frame(parent)
        self.__frame.pack()
        self.__text = ttk.Label(self.__frame, text="Charades", font=("Segoe UI", 35, "bold"))
        self.__text.pack()


class LobbyJoining:
    def __init__(self, parent, setLobbyCodeCallback):
        self.__setLobbyCode = setLobbyCodeCallback
        self.__frame = ttk.Frame(parent)
        self.__frame.pack()
        self.__lobbyCode = None

        self.__joinFrame = ttk.Frame(self.__frame)
        self.__joinFrame.grid(row=0, column=0, padx=10, pady=10)
        self.__label = ttk.Label(self.__joinFrame, text="Enter Lobby Code:", font=("Segoe UI", 15))
        self.__label.pack()
        self.__joinEntry = ttk.Entry(self.__joinFrame, font=("Consolas", 12))
        self.__joinEntry.pack()
        self.__joinNameLabel = ttk.Label(self.__joinFrame, text="Enter team name:", font=("Segoe UI", 12))
        self.__joinNameLabel.pack()
        self.__joinNameEntry = ttk.Entry(self.__joinFrame, font=("Segoe UI", 12))
        self.__joinNameEntry.pack()
        self.__button = ttk.Button(self.__joinFrame, text="Join", command=self.joinLobby)
        self.__button.pack()

        self.__newFrame = ttk.Frame(self.__frame)
        self.__newFrame.grid(row=0, column=1, padx=30,pady=10)
        self.__newLabel = ttk.Label(self.__newFrame, text="Create New Lobby:", font=("Segoe UI", 15))
        self.__newLabel.pack()
        self.__newNameLabel = ttk.Label(self.__newFrame, text="Enter team name:", font=("Segoe UI", 12))
        self.__newNameLabel.pack()
        self.__newNameEntry = ttk.Entry(self.__newFrame, font=("Segoe UI", 12))
        self.__newNameEntry.pack()
        self.__newButton = ttk.Button(self.__newFrame, text="New Lobby", command=self.newLobby)
        self.__newButton.pack()

    def joinLobby(self):
        lobbyCode = self.__joinEntry.get()
        print(f"Joining lobby: {lobbyCode}")
        teamName = self.__joinNameEntry.get()
        response = requests.get(f"http://{SERVER}/api/join-lobby?lobbyCode={lobbyCode}&clientName={teamName}")
        print(response.text)
        if response.status_code == 200:
            print("Successfully joined the lobby.")
            self.__setLobbyCode(lobbyCode)
        else:
            print("Failed to join the lobby.")
    
    def newLobby(self):
        teamName = self.__newNameEntry.get()
        print("Creating new lobby...")
        response = requests.get(f"http://{SERVER}/api/new-game?clientName={teamName}")
        if response.status_code == 200:
            lobbyCode = response.json().get("lobbyCode")
            print(f"New lobby created with code: {lobbyCode}")
            self.__lobbyCode = lobbyCode
            self.__setLobbyCode(lobbyCode)
        else:
            print("Failed to create a new lobby.")


class HostOptions:
    def __init__(self, parent, lobbyCode):
        self.__host = False
        self.__lobbyCode = lobbyCode
        self.__frame = ttk.Frame(parent)
        self.__frame.pack()
        self.__button = ttk.Button(self.__frame, text="Start Game", command=self.startGame)
        self.__button.pack()
        self.__button.config(state="disabled")
        self.__lobbyText = ttk.Label(self.__frame, text=f"Lobby Code: {self.__lobbyCode}", font=("Segoe UI", 15))
        self.__lobbyText.pack()

        self.__querying = True
        threading.Thread(target=self.queryLobby).start()

    def queryLobby(self):
        response = requests.get(f"http://{SERVER}/api/query-lobby?lobbyCode={self.__lobbyCode}")
        if len(response.json().get("clients")) == 1:
            self.__host = True
        while self.__querying:
            time.sleep(5)
            response = requests.get(f"http://{SERVER}/api/query-lobby?lobbyCode={self.__lobbyCode}")
            if response.status_code == 200:
                if len(response.json().get("clients")) == 2:
                    if self.__host:
                        self.__button.config(state="normal")
                    self.__querying = False
    
    def startGame(self):
        response = requests.get(f"http://{SERVER}/api/start-game?lobbyCode={self.__lobbyCode}")
        if response.status_code == 200:
            if response.json()

if __name__ == "__main__":
    screen = LobbyScreen(Window())
    screen.getWindow().mainloop()