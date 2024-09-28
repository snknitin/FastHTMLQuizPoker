from fasthtml.common import *
from collections import deque
import random
import string
from fasthtml.common import database as db
import asyncio
rooms = {}
messages = deque(maxlen=50)
users = {}



def centered_div(*content):
    return Div(*content, style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh;")

def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))


# app, rt = fast_app(db="teams.db", live=True, ws_hdr=True, pico=True, title=str, done=bool)

app, rt = fast_app(ws_hdr=True, pico=True)
db = database('teams.db')

# Create the teams table if it doesn't exist
if 'teams' not in db.t:
    db.t.teams.create(name=str, room=str, tokens=int, pk=['name', 'room'])

teams = db.t.teams
Team = teams.dataclass()


def token_display(room):
    team_tokens = db.t.teams(room=room)
    return Div(
        H3("Teams and Tokens"),
        *[Div(f"{team.name}: {team.tokens} tokens") for team in team_tokens],
        id='token-display'
    )


@rt('/select_card/{room}')
def post(room: str, card_select: str):
    if room not in rooms:
        return "Room not found"
    rooms[room]["current_card"] = card_select
    return f"Card selected: {card_select}"


@rt('/start_timer/{room}')
async def post(room: str, custom_time: int):
    if room not in rooms:
        return "Room not found"
    rooms[room]["timer"] = custom_time
    return f"Timer started: {custom_time} seconds"


async def update_timer(room):
    while rooms[room]["timer"] > 0:
        await asyncio.sleep(1)
        rooms[room]["timer"] -= 1
        for user in users.values():
            await user(f"Timer: {rooms[room]['timer']} seconds")
    for user in users.values():
        await user("Time's up!")


@app.get('/')
def homepage():
    return Titled("Quiz Game"), Container(
        H1("Welcome to the Quiz Game"),
        centered_div(
            Button("Create Room", hx_post="/create_room", hx_target="#room-creation"),
            Form(
                Input(name="room_id", placeholder="Enter Room ID"),
                Input(name="team_name", placeholder="Enter Team Name"),
                Button("Join Room", type="submit"),
                hx_post="/join_room"
            )
        ),
        Div(id="room-creation")  # This is where the room creation result will be inserted
    )


@app.post('/create_room')
def create_room():
    room = generate_room_code()
    rooms[room] = {
        "teams": {},
        "current_card": None,
        "timer": 60,
        "bids": {},
        "card_worth": 0
    }
    return Container(
        Grid(
            Div(
                H2(f"Room Created: {room}"),
                P("Share this code with your teams")
            ),
            Div(
                A("Enter Quiz Master Room", href=f"/qm/{room}", role="button"),
                style="display: flex; justify-content: flex-end; align-items: center;"
            )
        )
    )


@rt('/qm/{room}')
def get(room: str):
    if room not in rooms:
        return Titled("Room Not Found"), Container(
            H1("Room Not Found"),
            P("The requested room does not exist."),
            A("Back to Home", href="/", role="button")
        )

    return Titled(f"QM Room: {room}"), Container(
        Grid(
            Div(H1(f"Quiz Room: {room}")),
            Div(Div(id="timer", style="font-size: 1.5em; font-weight: bold;"), style="text-align: right;")
        ),
        Grid(
            Div(
                H3("Card Selection"),
                Select(
                    Option("Select a card", value=""),
                    *[Option(f"{value} of {suit}") for suit in ["Hearts", "Diamonds", "Clubs", "Spades"]
                      for value in ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King"]],
                    id="card-select"
                ),
                Button("Select Card", hx_post=f"/select_card/{room}", hx_include="#card-select"),
                Div(id="selected-card")
            ),
            Div(
                H3("Timer Control"),
                Input(type="number", name="custom_time", value="75", min="1", id="custom-time"),
                Button("Start Timer", hx_post=f"/start_timer/{room}", hx_include="#custom-time")
            )
        ),
        Grid(
            Div(
                H3("Bid Information"),
                Div(id="bids-list"),

                Div(id="priority-list")
            ),
            Div(
                H3("Token Display"),
                token_display(room)
            ),
            Div(
                H3("Game Controls"),
                Button("Get Priority", hx_post=f"/get_priority/{room}"),
                Button("Assign Winner", hx_post=f"/assign_winner/{room}"),
                Button("Clear Round", hx_post=f"/clear_round/{room}")
            ),
        ),
        Div(id="game-area", hx_ext='ws', ws_connect='/ws')
    )


def join_room(room_id: str, team_name: str):
    if room_id not in rooms:
        return False
    existing_team = db.t.teams.where(name=team_name, room=room_id).first()
    if existing_team:
        return False
    db.t.teams.insert(name=team_name, room=room_id, tokens=300)  # Initial tokens
    return True


@rt('/join_room')
def post(room_id: str, team_name: str):
    if join_room(room_id, team_name):
        return Container(
            Grid(
                Div(
                    H2(f"Joined Room: {room_id}"),
                    P(f"Team: {team_name}")
                ),
                Div(
                    A("Enter Team Room", href=f"/team/{room_id}/{team_name}", role="button"),
                    style="display: flex; justify-content: flex-end; align-items: center;"
                )
            )
        )
    return centered_div(P("Unable to join room. Room not found or team name already taken."))


@app.get('/team/{room}/{team}')
def team_room(room: str, team: str):
    team_record = db.t.teams(name=team, room=room).first()

    if room not in rooms or team not in rooms[room]["teams"]:
        return centered_div(P("Invalid room or team"))
    return Titled(f"Team Name: {team}"), Container(
        Grid(
            Div(
                P("Wow! What a great name"),
                P(f" Starting Tokens: {rooms[room]['teams'][team]}")
            ),
            H3("Current Card"),
            Div(id="current-card"),
            Div(Div(id="timer", style="font-size: 1.5em; font-weight: bold;"), style="text-align: right;")
        ),
        Grid(
            Div(
                H3("Bid Information"),
                Div(id="bids-list"),

                Div(id="priority-list")
            ),
            Div(
                H3("Token Display"),
                token_display(room)
            ),
            Div(
                Form(
                    Input(type="number", name="bid", min="1"),
                    Button("Place Bid", type="submit"),
                    hx_post=f"/place_bid/{room}/{team}"
                ),
            )
        ),
        Div(id="game-area", hx_ext='ws', ws_connect='/ws')
    )


@rt('/place_bid/{room}/{team}')
def post(room: str, team: str, bid: int):
    current_tokens = get_team_tokens(room, team)
    if current_tokens is None or current_tokens < bid:
        return "Not enough tokens"
    rooms[room]["bids"][team] = bid
    update_tokens(room, team, -bid)  # Deduct bid amount from team's tokens
    return f"{team} placed a bid of {bid}"


@rt('/assign_winner/{room}')
def post(room: str, winning_team: str):
    if room not in rooms or not db.t.teams.where(name=winning_team, room=room).exists():
        return "Invalid room or team"
    card_worth = rooms[room]["card_worth"]
    update_tokens(room, winning_team, card_worth)
    return f"{winning_team} won {card_worth} tokens!"


def update_tokens(room: str, team: str, amount: int):
    team_record = db.t.teams(name=team, room=room).first()
    if team_record:
        db.t.teams.update({'tokens': team_record.tokens + amount}, id=team_record.id)


def get_team_tokens(room: str, team: str):
    team_record = db.t.teams(name=team, room=room).first()
    return team_record.tokens if team_record else None


def update_all_clients(room, message):
    for user in users.values():
        user(message)
    return message


async def update_all_clients_async(room, message):
    for user in users.values():
        await user(message)


def on_connect(ws, send):
    users[id(ws)] = send


def on_disconnect(ws):
    users.pop(id(ws), None)


@app.ws('/ws', conn=on_connect, disconn=on_disconnect)
async def ws(msg: str, send):
    if msg.startswith("Token update:"):
        room = msg.split(":")[1].strip()
        await send(token_display(room))
    elif msg.startswith("New card selected:"):
        await send(Div(msg, id="current-card"))
    elif msg.startswith("Timer:"):
        await send(Div(msg, id="timer"))
    elif msg == "Time's up!":
        await send(Div(msg, id="timer"))
    else:
        await send(f"Received: {msg}")


serve()