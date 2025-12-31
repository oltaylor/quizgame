import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import jsonGetter
import asyncio

app = FastAPI()

activeLobbies = []

class Lobby:
    def __init__(self, lobbyCode: str):
        self.lobbyCode = lobbyCode
        self.clients = {}
        self.host = None
        self.__roundCount = 1

    def addClient(self, clientID: str, websocket: WebSocket):
        self.clients[clientID] = Client(clientID, websocket)
        if len(self.clients) == 1:
            self.host = clientID

    def getCode(self):
        return self.lobbyCode
    
    def startTimer(self):
        async def timer(self):
            await asyncio.sleep(90)
            if self.__roundCount < 4:
                self.__roundCount += 1
                # Send round ended message to all clients
                for client in self.clients.values():
                    await client.getWebSocket().send_json({"status": "roundEnded"})
                await asyncio.sleep(120)
                await client.getWebSocket().send_json({"status": "restart"})
                asyncio.create_task(timer(self))
            else:
                # Send game ended message to all clients
                for client in self.clients.values():
                    await client.getWebSocket().send_json({"status": "gameEnded"})
        asyncio.create_task(timer(self))
    
class Client:
    def __init__(self, clientID: str, websocket: WebSocket):
        self.__clientID = clientID
        self.__websocket = websocket
        self.__points = 0
        self.__answeredUIDs = []
    
    def getClientID(self):
        return self.__clientID
    
    def getWebSocket(self):
        return self.__websocket
    
    def getPoints(self):
        return self.__points
    
    def addPoints(self, points: int):
        self.__points += points
    
    def getAnsweredUIDs(self):
        return self.__answeredUIDs
    
    def addAnsweredUID(self, uid: int):
        self.__answeredUIDs.append(uid)

@app.websocket("/ws/{lobbyCode}/{clientID}")
async def websocketEndpoint(websocket: WebSocket, lobbyCode: str, clientID: str): # subroutine for handling connections
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

                answeredUIDs = lobby.clients[clientID].getAnsweredUIDs()
                
                gamemode, task = await genTask()
                uid = task["uid"]

                attempts = 0
                max_attempts = 100
                while uid in answeredUIDs and attempts < max_attempts:
                    gamemode, task = await genTask()
                    uid = task["uid"]
                    attempts += 1
                
                if attempts < max_attempts:
                    lobby.clients[clientID].addAnsweredUID(uid)
                    await websocket.send_json({"type": gamemode, "task": task})
                else:
                    # All tasks answered, send error or reset
                    await websocket.send_json({"status": "error", "errorMessage": "All tasks completed"})
                
                

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
                        lobby.startTimer()
            
            elif command == "requestScores":
                for lobby in activeLobbies:
                    if lobby.getCode() == lobbyCode:
                        scores = {client.getClientID(): client.getPoints() for client in lobby.clients.values()}
                        await websocket.send_json({"scores": scores})

            else:
                print(f"Unknown command from {clientID} in lobby {lobbyCode}: {command}")
                await websocket.send_json({"status": "error", "errorMessage": "Unknown command"})

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

async def genTask():
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

    return gamemode, task

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=676)