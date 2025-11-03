import requests
import time
import tkinter as tk
from tkinter import ttk

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
        self.__title = Title(self.__window.getWindow())
        self.__lobbyJoining = LobbyJoining(self.__window.getWindow())
    
    def getWindow(self):
        return self.__window.getWindow()


class Title:
    def __init__(self, parent):
        self.__frame = ttk.Frame(parent)
        self.__frame.pack()
        self.__text = ttk.Label(self.__frame, text="Charades", font=("Segoe UI", 35, "bold"))
        self.__text.pack()


class LobbyJoining:
    def __init__(self, parent):
        self.__frame = ttk.Frame(parent)
        self.__frame.pack()

        self.__joinFrame = ttk.Frame(self.__frame)
        self.__joinFrame.grid(row=0, column=0, padx=10, pady=10)
        self.__label = ttk.Label(self.__joinFrame, text="Enter Lobby Code:", font=("Segoe UI", 15))
        self.__label.pack()
        self.__joinEntry = ttk.Entry(self.__joinFrame, font=("Segoe UI", 15))
        self.__joinEntry.pack()
        self.__joinNameLabel = ttk.Label(self.__joinFrame, text="Enter team name:", font=("Segoe UI", 12))
        self.__joinNameLabel.pack()
        self.__joinNameEntry = ttk.Entry(self.__joinFrame, font=("Segoe UI", 12))
        self.__joinNameEntry.pack()
        self.__button = ttk.Button(self.__joinFrame, text="Join", command=lambda: self.joinLobby(self.__joinEntry.get()))
        self.__button.pack()

        self.__newFrame = ttk.Frame(self.__frame)
        self.__newFrame.grid(row=0, column=1, padx=10, pady=10)
        self.__newLabel = ttk.Label(self.__newFrame, text="Create New Lobby:", font=("Segoe UI", 15))
        self.__newLabel.pack()
        self.__newNameLabel = ttk.Label(self.__newFrame, text="Enter team name:", font=("Segoe UI", 12))
        self.__newNameLabel.pack()
        self.__newNameEntry = ttk.Entry(self.__newFrame, font=("Segoe UI", 12))
        self.__newNameEntry.pack()
        self.__newButton = ttk.Button(self.__newFrame, text="New Lobby", command=self.newLobby)
        self.__newButton.pack()

    def joinLobby(self, lobbyCode):
        print(f"Joining lobby: {lobbyCode}")
        teamName = self.__joinNameEntry.get()
        response = requests.get(f"http://{SERVER}/api/join-lobby?lobbyCode={lobbyCode}&teamName={teamName}")
        if response.status_code == 200:
            print("Successfully joined the lobby.")
        else:
            print("Failed to join the lobby.")
    
    def newLobby(self):
        teamName = self.__newNameEntry.get()
        print("Creating new lobby...")
        response = requests.get(f"http://{SERVER}/api/new-game?clientName={teamName}")
        if response.status_code == 200:
            lobbyCode = response.json().get("lobbyCode")
            print(f"New lobby created with code: {lobbyCode}")
        else:
            print("Failed to create a new lobby.")


if __name__ == "__main__":
    screen = LobbyScreen(Window())
    screen.getWindow().mainloop()