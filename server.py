import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from asyncio import sleep
import jsonGetter

app = FastAPI()

activeLobbies = []

class Lobby:
    def __init__(self, lobbyCode: str):
        self.lobbyCode = lobbyCode
        self.clients = {}
        self.host = None

    def addClient(self, clientID: str, websocket: WebSocket):
        self.clients[clientID] = Client(clientID, websocket)
        if len(self.clients) == 1:
            self.host = clientID

    def getCode(self):
        return self.lobbyCode
    
class Client:
    def __init__(self, clientID: str, websocket: WebSocket):
        self.__clientID = clientID
        self.__websocket = websocket
        self.__points = 0
    
    def getClientID(self):
        return self.__clientID
    
    def getWebSocket(self):
        return self.__websocket
    
    def getPoints(self):
        return self.__points
    
    def addPoints(self, points: int):
        self.__points += points

@app.websocket("/ws/{lobbyCode}/{clientID}")
async def websocket_endpoint(websocket: WebSocket, lobbyCode: str, clientID: str): # subroutine for handling connections
    await websocket.accept() # accept the connection of any incoming client
    if lobbyCode not in [lobby.getCode() for lobby in activeLobbies]:
        # create lobby if not exists
        newLobby = Lobby(lobbyCode)
        activeLobbies.append(newLobby)

    # add client to lobby
    for lobby in activeLobbies:
        if lobby.getCode() == lobbyCode:
            lobby.addClient(clientID, websocket)
            print(f"Client {clientID} joined lobby {lobbyCode}")
            await websocket.send_json({"status": "lobbyJoined", "lobbyCode": lobbyCode, "clientID": clientID, "isHost": lobby.host == clientID})
            for client in lobby.clients.values():
                await client.getWebSocket().send_json({"status": "teamUpdate", "teamNames": list(lobby.clients.keys())})
    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received from {clientID} in lobby {lobbyCode}: {data}")

            command = data.get("command")

            if command == "newTask":
                gamemode = random.choice(["charades", "quiz", "whoami"])
                if gamemode == "quiz":
                    print("Generating new quiz question")
                    task = jsonGetter.getQuestion()
                elif gamemode == "charades":
                    print("Generating new charades prompt")
                    task = jsonGetter.getCharade()
                elif gamemode == "whoami":
                    print("Generating new whoami prompt")
                    task = jsonGetter.getWhoAmI()
                await websocket.send_json({"type": gamemode, "task": task})

            elif command == "addPoints":
                points = data.get("points", 0) # default to 0 if not provided
                for lobby in activeLobbies:
                    if lobby.getCode() == lobbyCode:
                        client = lobby.clients.get(clientID)
                        if client:
                            client.addPoints(points)
                            print(f"Client {clientID} in lobby {lobbyCode} now has {client.getPoints()} points")
            
            elif command == "start":
                print(f"Starting game in lobby {lobbyCode}")
                for lobby in activeLobbies:
                    if lobby.getCode() == lobbyCode:
                        for client in lobby.clients.values():
                            await client.getWebSocket().send_json({"status": "start"})

    except WebSocketDisconnect:
        print(f"Client {clientID} disconnected from lobby {lobbyCode}")
        for lobby in activeLobbies:
            if lobby.getCode() == lobbyCode:
                if clientID in lobby.clients:
                    del lobby.clients[clientID]
                    for client in lobby.clients.values():
                        await client.getWebSocket().send_json({"status": "teamUpdate", "teamNames": list(lobby.clients.keys())})
                if len(lobby.clients) == 0:
                    activeLobbies.remove(lobby)
                    print(f"Lobby {lobbyCode} removed due to no active clients")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)