from fastapi import FastAPI
import random
import string

app = FastAPI()

activeGames = []

class Game:
    def __init__(self):
        self.__lobbyCode = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        self.__clients = []
        self.__status = "waiting" # waiting (for clients), waiting to start, in progress
    
    def addClient(self, client):
        self.__clients.append(client)

    def removeClient(self, client):
        self.__clients.remove(client)

    def getLobbyCode(self):
        return self.__lobbyCode
    
    def setStatus(self, status: str):
        self.__status = status
    
    def getStatus(self):
        return self.__status

    def getClients(self):
        return [client.getTeamName() for client in self.__clients]
    
    def __str__(self):
        return f"Lobby: {self.__lobbyCode}"

class Client:
    def __init__(self, teamName: str):
        self.__teamName = teamName
    
    def setTeamName(self, teamName: str):
        self.__teamName = teamName
    
    def getTeamName(self):
        return self.__teamName
    
    def __str__(self):
        return f"Client: {self.__teamName}"

@app.get("/")
def home():
    return {"message": "Welcome to the Charades API."}

@app.get("/api/new-game")
def newGame(clientName = None):
    if clientName:
        game = Game()
        activeGames.append(game)
        game.addClient(Client(clientName))
        return {"lobbyCode": game.getLobbyCode()}
    else:
        return {"error": "Client name is required to create a new game."}

@app.get("/api/query-lobby")
def queryLobby(lobbyCode: str):
    if lobbyCode:
        for game in activeGames:
            if game.getLobbyCode() == lobbyCode:
                return {"status": game.getStatus(), "lobbyCode": game.getLobbyCode(), "clients": game.getClients()}
        return {"error": "Lobby not found."}
    return {"error": "Lobby code is required to query a lobby."}

@app.get("/api/join-lobby")
def joinLobby(lobbyCode: str, clientName: str):
    if lobbyCode and clientName:
        for game in activeGames:
            if game.getLobbyCode() == lobbyCode:
                game.addClient(Client(clientName))
                return {"message": f"{clientName} joined lobby {lobbyCode}."}
        return {"error": "Lobby not found."}
    return {"error": "Lobby code and client name are required to join a lobby."}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)