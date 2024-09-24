# import json
#
from fasthtml.common import *
# from collections import deque
import random
import string
# import asyncio
#
# app = FastHTML(ws_hdr=True, live=True)


app,rt = fast_app(live=True)

rooms = {}
users = {}

def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

def centered_div(*content):
    return Div(*content, style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh;")



# @rt('/')
# def get(): return Div(P('Hello World 2!'), hx_get="/change")

@rt('/change')
def get(): return P('RoomCode is ' + generate_room_code())



@rt('/')
def homepage():
    return Titled("Quiz Poker"), centered_div(
        H1("Welcome to the Quiz Game"),
        Button("Create Room", hx_post="/create_room"),
        Form(
            Input(name="room_id", placeholder="Enter Room ID"),
            Input(name="team_name", placeholder="Enter Team Name"),
            Button("Join Room", type="submit"),
            hx_post="/join_room"
        )
    )



@rt('/create_room')
def create_room():
    room = generate_room_code()
    rooms[room] = {
        "teams": {},
        "current_card": None,
        "timer": 75,
        "bids": {},
        "card_worth": 0
    }
    return centered_div(
        H2(f"Room Created: {room}"),
        P("Share this code with your teams"),
        A("Enter Quiz Master Room", href=f"/qm/{room}")
    )



@rt('/join_room')
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

@rt('/qm/{room}')
def qm_room(room: str):
    if room not in rooms:
        return centered_div(P("Room not found"))
    return Titled(f"QM Room: {room}"), centered_div(
        H2(f"Quiz Master Room: {room}"),
        Div(id="teams-list"),
        Select(
            Option("Select a card", value=""),
            *[Option(f"{value} of {suit}") for suit in ["Hearts", "Diamonds", "Clubs", "Spades"]
              for value in ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King"]],
            id="card-select"
        ),
        Button("Select Card", hx_post=f"/select_card/{room}", hx_include="#card-select"),
        Div(
            Input(type="number", name="custom_time", value="75", min="1"),
            Button("Start Timer", hx_post=f"/start_timer/{room}")
        ),
        Div(id="timer"),
        Div(id="bids-list"),
        Button("Get Priority", hx_post=f"/get_priority/{room}"),
        Div(id="priority-list"),
        Button("Clear Round", hx_post=f"/clear_round/{room}"),
        Div(id="game-area")
    )


serve()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)



# @app.get('/team/{room}/{team}')
# def team_room(room: str, team: str):
#     if room not in rooms or team not in rooms[room]["teams"]:
#         return centered_div(P("Invalid room or team"))
#     return Titled(f"Team Room: {team}"), centered_div(
#         H2(f"Team Room: {team}"),
#         P(f"Room: {room}"),
#         P(f"Tokens: {rooms[room]['teams'][team]}"),
#         Div(id="current-card"),
#         Div(id="timer"),
#         Form(
#             Input(type="number", name="bid", min="1"),
#             Button("Place Bid", type="submit"),
#             hx_post=f"/place_bid/{room}/{team}"
#         ),
#         Div(id="bids-list"),
#         Div(id="game-area")
#     )
#
# @app.post('/select_card/{room}')
# def select_card(room: str, card: str):
#     if room not in rooms:
#         return P("Room not found")
#     rooms[room]["current_card"] = card
#     rooms[room]["bids"] = {}
#     rooms[room]["card_worth"] = 0
#     return Div(
#         P(f"Selected Card: {card}"),
#         _=f"htmx.trigger('#current-card', 'cardSelected', {{card: '{card}'}})"
#     )
#
# @app.post('/start_timer/{room}')
# def start_timer(room: str, custom_time: int):
#     if room not in rooms:
#         return P("Room not found")
#     rooms[room]["timer"] = custom_time
#     asyncio.create_task(run_timer(room))
#     return P(f"Timer started: {custom_time} seconds")
#
# @app.post('/place_bid/{room}/{team}')
# def place_bid(room: str, team: str, bid: int):
#     if room not in rooms or team not in rooms[room]["teams"]:
#         return P("Invalid room or team")
#     if rooms[room]["teams"][team] < bid:
#         return P("Insufficient tokens")
#     rooms[room]["bids"][team] = bid
#     rooms[room]["teams"][team] -= bid
#     return Div(
#         P(f"Bid placed: {bid}"),
#         P(f"Tokens left: {rooms[room]['teams'][team]}"),
#         _=f"htmx.trigger('#bids-list', 'bidPlaced', {{team: '{team}', bid: {bid}}})"
#     )
#
# @app.post('/get_priority/{room}')
# def get_priority(room: str):
#     if room not in rooms:
#         return P("Room not found")
#     sorted_bids = sorted(rooms[room]["bids"].items(), key=lambda x: x[1], reverse=True)
#     rooms[room]["card_worth"] = sum(rooms[room]["bids"].values())
#     return Div(
#         H3("Priority List"),
#         Table(
#             Tr(Th("Team"), Th("Bid"), Th("Priority")),
#             *[Tr(Td(team), Td(bid), Td(i+1)) for i, (team, bid) in enumerate(sorted_bids)]
#         ),
#         P(f"Card Worth: {rooms[room]['card_worth']}")
#     )
#
# @app.post('/clear_round/{room}')
# def clear_round(room: str):
#     if room not in rooms:
#         return P("Room not found")
#     rooms[room]["bids"] = {}
#     rooms[room]["current_card"] = None
#     rooms[room]["card_worth"] = 0
#     rooms[room]["timer"] = 75
#     return Div(
#         P("Round cleared"),
#         _="htmx.trigger('body', 'roundCleared')"
#     )
#
# async def run_timer(room: str):
#     while rooms[room]["timer"] > 0:
#         await asyncio.sleep(1)
#         rooms[room]["timer"] -= 1
#         for user in users.values():
#             await user(P(f"Time left: {rooms[room]['timer']} seconds", id="timer", hx_swap_oob="true"))
#     for user in users.values():
#         await user(P("Time's up!", id="timer", hx_swap_oob="true"))
#
# def on_connect(ws, send):
#     users[id(ws)] = send
#
# def on_disconnect(ws):
#     users.pop(id(ws), None)
#
# @app.ws('/ws', conn=on_connect, disconn=on_disconnect)
# async def ws(msg: str, send):
#     data = json.loads(msg)
#     room = data.get('room')
#     if room in rooms:
#         if data.get('type') == 'cardSelected':
#             for user in users.values():
#                 await user(P(f"Current Card: {data['card']}", id="current-card", hx_swap_oob="true"))
#         elif data.get('type') == 'bidPlaced':
#             for user in users.values():
#                 await user(Div(P(f"{data['team']} bid {data['bid']}"), id="bids-list", hx_swap_oob="innerHTML"))
#         elif data.get('type') == 'roundCleared':
#             for user in users.values():
#                 await user(Div(id="bids-list", hx_swap_oob="innerHTML"))
#                 await user(P("", id="current-card", hx_swap_oob="true"))
#                 await user(P("75 seconds", id="timer", hx_swap_oob="true"))
#
# serve()