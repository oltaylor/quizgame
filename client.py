import requests
import time

if __name__ == "__main__":
    answer = input("1. new game\n2. join game")
    if answer == "1":
        teamName = input("Enter team name: ")
        server = input("Enter server address: ")
        response = requests.get(f"http://{server}/api/new-game?clientName={teamName}")
        responseData = response.json()
        lobbyCode = responseData.get("lobbyCode")
        print(response.text)
    elif answer == "2":
        teamName = input("Enter team name: ")
        lobbyCode = input("Enter lobby code: ")
        server = input("Enter server address: ")
        response = requests.get(f"http://{server}/api/join-lobby?lobbyCode={lobbyCode}&clientName={teamName}")
        print(response.text)
    while True:
        time.sleep(5)
        response = requests.get(f"http://{server}/api/query-lobby?lobbyCode={lobbyCode}")
        print(f"\n\n{response.text}")