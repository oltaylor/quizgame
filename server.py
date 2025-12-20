import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from asyncio import sleep
import json
import jsonGetter

app = FastAPI()

activeLobbies = []

class Lobby:
    def __init__(self, lobbyCode: str):
        self.lobbyCode = lobbyCode
        self.clients = {}
        self.host = None

    def addClient(self, clientID: str, websocket: WebSocket):
        self.clients[clientID] = websocket
        if len(self.clients) == 1:
            self.host = clientID

    def getCode(self):
        return self.lobbyCode

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

    except WebSocketDisconnect:
        print(f"Client {clientID} disconnected from lobby {lobbyCode}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)