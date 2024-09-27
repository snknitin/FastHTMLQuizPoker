from fasthtml.common import *
from collections import deque
import random
import string

app, rt = fast_app(ws_hdr=True)

rooms = {}
users = {}

def centered_div(*content):
    return Div(*content, style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh;")

def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

@app.get('/')
def homepage():
    return Titled("Quiz Game"), Container(
        H1("Welcome to the Quiz Game"),
        Div(
            Button("Create Room", hx_post="/create_room"),
             Form(
                Input(name="room_id", placeholder="Enter Room ID"),
                Input(name="team_name", placeholder="Enter Team Name"),
                Button("Join Room", type="submit"),
                hx_post="/join_room")
        )
    )

@app.post('/create_room')
def create_room():
    room = generate_room_code()
    rooms[room] = {"teams": {}}
    return centered_div(
        H2(f"Room Created: {room}"),
        P("Share this code with your teams"),
        A("Enter Quiz Master Room", href=f"/qm/{room}")
    )

@app.post('/join_room')
def join_room(room_id: str, team_name: str):
    if room_id not in rooms:
        return centered_div(P("Room not found"))
    if team_name in rooms[room_id]["teams"]:
        return centered_div(P("Team name already taken"))
    rooms[room_id]["teams"][team_name] = 300  # Initial tokens
    return centered_div(
        H2(f"Joined Room: {room_id}"),
        P(f"Team: {team_name}"),
        A("Enter Team Room", href=f"/team/{room_id}/{team_name}")
    )

@app.get('/qm/{room}')
def qm_room(room: str):
    if room not in rooms:
        return centered_div(P("Room not found"))
    return Titled(f"QM Room: {room}"), centered_div(
        H2(f"Quiz Master Room: {room}"),
        Div(id="teams-list"),
        Button("Start Game", hx_post=f"/start_game/{room}"),
        Div(id="game-area")
    )

@app.get('/team/{room}/{team}')
def team_room(room: str, team: str):
    if room not in rooms or team not in rooms[room]["teams"]:
        return centered_div(P("Invalid room or team"))
    return Titled(f"Team Room: {team}"), centered_div(
        H2(f"Team Room: {team}"),
        P(f"Room: {room}"),
        P(f"Tokens: {rooms[room]['teams'][team]}"),
        Div(id="game-area")
    )

@app.post('/start_game/{room}')
def start_game(room: str):
    if room not in rooms:
        return P("Room not found")
    return Div(
        H3("Game Started"),
        P("Waiting for first question...")
    )

def on_connect(ws, send):
    users[id(ws)] = send

def on_disconnect(ws):
    users.pop(id(ws), None)

@app.ws('/ws', conn=on_connect, disconn=on_disconnect)
async def ws(msg: str, send):
    # Handle WebSocket messages here
    pass

serve()