from fastapi import FastAPI
from fasthtml import fasthtml
import uvicorn
import random
import string
import asyncio
import json

app = FastAPI()

# Game state
rooms = {}

# WebSocket connections
connections = {}


def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))


@app.get("/")
@fasthtml
async def index():
    return """
    <html>
        <head>
            <title>Quiz Game</title>
        </head>
        <body>
            <h1>Welcome to the Quiz Game</h1>
            <button @click="create_room">Create Room as QM</button>
            <div>
                <input type="text" :value="room_id" @input="room_id = $event.target.value" placeholder="Enter Room ID">
                <input type="text" :value="team_name" @input="team_name = $event.target.value" placeholder="Enter Team Name">
                <button @click="join_room">Join Room</button>
            </div>
            <script>
                fasthtml.setup({
                    data: {
                        room_id: '',
                        team_name: ''
                    },
                    methods: {
                        create_room: function() {
                            fetch('/create_room', {method: 'POST'})
                                .then(response => response.json())
                                .then(data => window.location.href = `/qm/${data.room}`);
                        },
                        join_room: function() {
                            if (this.room_id && this.team_name) {
                                localStorage.setItem('team', this.team_name);
                                window.location.href = `/team/${this.room_id}`;
                            } else {
                                alert('Please enter both Room ID and Team Name');
                            }
                        }
                    }
                });
            </script>
        </body>
    </html>
    """


@app.get("/qm/{room}")
@fasthtml
async def qm_room(room: str):
    if room not in rooms:
        return """
        <script>
            window.location.href = '/';
        </script>
        """
    return f"""
    <html>
        <head>
            <title>Quiz Master Room</title>
        </head>
        <body>
            <h1>Quiz Master Room: {room}</h1>
            <div>
                <select :value="selected_card" @input="selected_card = $event.target.value">
                    <option value="">Select a card</option>
                    <option v-for="card in cards" :value="card">{{card}}</option>
                </select>
                <button @click="select_card">Select Card</button>
            </div>
            <div>
                <input type="number" :value="custom_time" @input="custom_time = $event.target.value" min="1">
                <button @click="start_timer">Start Timer</button>
                <span>{{timer}} seconds left</span>
            </div>
            <div>
                <h2>Teams</h2>
                <div v-for="(tokens, team) in teams">{{team}}: {{tokens}} tokens</div>
            </div>
            <div>
                <h2>Bids</h2>
                <div v-for="(bid, team) in bids">{{team}} bid {{bid.amount}} ({{bid.time}}s left)</div>
            </div>
            <button @click="get_priority">Get Priority</button>
            <div v-if="priority_list">
                <h2>Priority List</h2>
                <table>
                    <tr><th>Team</th><th>Bid</th><th>Time</th><th>Priority</th></tr>
                    <tr v-for="(bid, index) in priority_list">
                        <td>{{bid[0]}}</td>
                        <td>{{bid[1].amount}}</td>
                        <td>{{bid[1].time}}</td>
                        <td>{{index + 1}}</td>
                    </tr>
                </table>
            </div>
            <div>
                <select :value="winner" @input="winner = $event.target.value">
                    <option value="no_winner">No Winner</option>
                    <option v-for="team in Object.keys(teams)" :value="team">{{team}}</option>
                </select>
                <button @click="assign_winner">Assign Winner</button>
            </div>
            <button @click="clear_round">Clear Round</button>
            <script>
                fasthtml.setup({{
                    data: {{
                        room: '{room}',
                        selected_card: '',
                        custom_time: 75,
                        timer: 75,
                        teams: {{}},
                        bids: {{}},
                        priority_list: null,
                        winner: 'no_winner',
                        cards: ['Ace of Spades', 'King of Hearts', '10 of Diamonds', '2 of Clubs'] // Add all 52 cards here
                    }},
                    methods: {{
                        select_card: function() {{
                            fetch('/select_card', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify({{room: this.room, card: this.selected_card}})
                            }});
                        }},
                        start_timer: function() {{
                            fetch('/start_timer', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify({{room: this.room, custom_time: this.custom_time}})
                            }});
                        }},
                        get_priority: function() {{
                            fetch('/get_priority', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify({{room: this.room}})
                            }})
                            .then(response => response.json())
                            .then(data => this.priority_list = data.bids);
                        }},
                        assign_winner: function() {{
                            fetch('/assign_winner', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify({{room: this.room, winner: this.winner}})
                            }});
                        }},
                        clear_round: function() {{
                            fetch('/clear_round', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify({{room: this.room}})
                            }});
                        }}
                    }}
                }});

                const eventSource = new EventSource('/sse/{room}');
                eventSource.onmessage = function(event) {{
                    const data = JSON.parse(event.data);
                    Object.assign(fasthtml.$data, data);
                }};
            </script>
        </body>
    </html>
    """


@app.get("/team/{room}")
@fasthtml
async def team_room(room: str):
    if room not in rooms:
        return """
        <script>
            window.location.href = '/';
        </script>
        """
    return f"""
    <html>
        <head>
            <title>Team Room</title>
        </head>
        <body>
            <h1>Team Room: {room}</h1>
            <h2>Team: {{team}}</h2>
            <div>Current Card: {{current_card}}</div>
            <div>{{timer}} seconds left</div>
            <div>
                <h2>Teams</h2>
                <div v-for="(tokens, team) in teams">{{team}}: {{tokens}} tokens</div>
            </div>
            <div>
                <h2>Bids</h2>
                <div v-for="(bid, team) in bids">{{team}} bid {{bid.amount}} ({{bid.time}}s left)</div>
            </div>
            <div>
                <input type="number" :value="bid_amount" @input="bid_amount = $event.target.value" min="1">
                <button @click="place_bid">Place Bid</button>
            </div>
            <script>
                fasthtml.setup({{
                    data: {{
                        room: '{room}',
                        team: localStorage.getItem('team'),
                        current_card: '',
                        timer: 75,
                        teams: {{}},
                        bids: {{}},
                        bid_amount: 0
                    }},
                    methods: {{
                        place_bid: function() {{
                            fetch('/place_bid', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify({{room: this.room, team: this.team, bid: parseInt(this.bid_amount)}})
                            }});
                        }}
                    }}
                }});

                const eventSource = new EventSource('/sse/{room}');
                eventSource.onmessage = function(event) {{
                    const data = JSON.parse(event.data);
                    Object.assign(fasthtml.$data, data);
                }};
            </script>
        </body>
    </html>
    """


@app.post("/create_room")
async def create_room():
    room = generate_room_code()
    while room in rooms:
        room = generate_room_code()
    rooms[room] = {"teams": {}, "current_card": None, "timer": 75, "bids": {}, "card_worth": 0}
    return {"room": room}


@app.post("/select_card")
async def select_card(data: dict):
    room = data['room']
    card = data['card']
    if room in rooms:
        rooms[room]['current_card'] = card
        rooms[room]['bids'] = {}
        rooms[room]['card_worth'] = 0
        await broadcast(room)


@app.post("/start_timer")
async def start_timer(data: dict):
    room = data['room']
    custom_time = data.get('custom_time', 75)
    if room in rooms:
        rooms[room]['timer'] = int(custom_time)
        asyncio.create_task(run_timer(room))


@app.post("/place_bid")
async def place_bid(data: dict):
    room = data['room']
    team = data['team']
    bid = data['bid']
    if room in rooms and team in rooms[room]['teams']:
        if rooms[room]['teams'][team] >= bid:
            rooms[room]['bids'][team] = {"amount": bid, "time": rooms[room]['timer']}
            rooms[room]['teams'][team] -= bid
            await broadcast(room)
        else:
            return {"error": "Insufficient tokens"}


@app.post("/get_priority")
async def get_priority(data: dict):
    room = data['room']
    if room in rooms:
        sorted_bids = sorted(rooms[room]['bids'].items(), key=lambda x: (-x[1]['amount'], x[1]['time']))
        rooms[room]['card_worth'] = sum(bid['amount'] for bid in rooms[room]['bids'].values())
        return {"bids": sorted_bids, "card_worth": rooms[room]['card_worth']}


@app.post("/assign_winner")
async def assign_winner(data: dict):
    room = data['room']
    winner = data['winner']
    if room in rooms:
        if winner != "no_winner":
            rooms[room]['teams'][winner] += rooms[room]['card_worth']
        await broadcast(room)


@app.post("/clear_round")
async def clear_round(data: dict):
    room = data['room']
    if room in rooms:
        rooms[room]['bids'] = {}
        rooms[room]['current_card'] = None
        rooms[room]['card_worth'] = 0
        rooms[room]['timer'] = 75
        await broadcast(room)


@app.get("/sse/{room}")
async def sse(room: str):
    async def event_generator():
        if room not in connections:
            connections[room] = set()
        connections[room].add(asyncio.current_task())
        try:
            while True:
                if room in rooms:
                    yield f"data: {json.dumps(rooms[room])}\n\n"
                await asyncio.sleep(1)
        finally:
            connections[room].remove(asyncio.current_task())

    return fasthtml.streaming_response(event_generator())


async def broadcast(room: str):
    if room in connections:
        for connection in connections[room]:
            if not connection.done():
                connection.cancel()


async def run_timer(room: str):
    while rooms[room]['timer'] > 0:
        await asyncio.sleep(1)
        rooms[room]['timer'] -= 1
        await broadcast(room)
    await broadcast(room)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)