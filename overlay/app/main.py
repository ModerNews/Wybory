import datetime
import json
import hashlib
import logging

from logging.config import dictConfig
from typing import Optional

import uvicorn

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from Models import *

app = FastAPI()

app.mount("/static", StaticFiles(directory="../static"), name="static")
# templates = Jinja2Templates(directory="../templates")
global timer
global info_bar
global emble_visible
global map_state
timer: TimerState = TimerState()
info_bar = []
emblem_visible = False
map_state = {"visible": False,
             "team1": "",
             "team2": ""}


with open("strings.txt") as file:
    predefs = [item.strip() for item in file.read().split("\n")]

with open("candidates.txt") as file:
    candidates = [item.strip() for item in file.read().split("\n")]


def UpdateTimer():
    if timer.running:
        now = datetime.datetime.now()
        timer_val = (now - timer.started_at).total_seconds()

        timer.time = max(timer.time - timer_val, 0)

        timer.started_at = now


@app.get("/")
async def index_loader(request: Request, team1: str = "Nieznana", team2: str = "Nieznana"):
    # return templates.TemplateResponse("index.html", {"request": request, "team1": team1.replace("_", " "), "team2": team2.replace("_", " ")})
    with open('../templates/index.html', encoding='utf8') as file:
        data = file.read()
    return HTMLResponse(data)


@app.get("/controller")
async def main_controller(request: Request):
    # return templates.TemplateResponse("controller.html", {"request": request})
    with open('../templates/controller.html', encoding='utf8') as file:
        data = file.read()
    return HTMLResponse(data)

@app.get("/tournament")
async def tournament_view(request: Request):
    # return templates.TemplateResponse('tournament-table.html', {"request": request})
    with open('../templates/tournament-table.html', encoding='utf8') as file:
        data = file.read()
    return HTMLResponse(data)


# region Websockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_text(self, message: str, *, websocket: Optional[WebSocket] = None):
        if websocket is None:
            for connection in self.active_connections:
                await connection.send_text(message)
            return {"code": 200, "message": message, "times_send": len(self.active_connections)}
        await websocket.send_text(message)
        return {"code": 200, "message": message, "times_send": 1}

    async def send_json(self, message: dict, *, websocket: Optional[WebSocket] = None):
        if websocket is None:
            for connection in self.active_connections:
                await connection.send_json(message)
            return {"code": 200, "message": message, "times_send": len(self.active_connections)}
        await websocket.send_json(message)
        return {"code": 200, "message": message, "times_send": 1}


manager = ConnectionManager()


@app.websocket("/websocket")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"event": "infobar", "content": info_bar})
    await websocket.send_json({"event": "show_emblem", "value": emblem_visible})
    await websocket.send_json({"event": "predefs", "content": predefs})
    await websocket.send_json({"event": "candidates", "content": candidates})
    await websocket.send_json({"event": "timer_state", "state": timer.__dict__()})
    await websocket.send_json({"event": "maps_state", "state": map_state})
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            print(data)
            if data["event"] == "timer":
                if data["type"] == "start" and not timer.running:
                    timer.running = True
                    timer.started_at = datetime.datetime.now()
                    await manager.send_json({"event": "timer_state", "state": timer.__dict__()})
                elif data["type"] == "stop":
                    UpdateTimer()
                    timer.running = False
                    await manager.send_json({"event": "timer_state", "state": timer.__dict__()})

                elif["type"] == "set":
                    timer.running = False
                    timer.time = int(data["time"])
                    await manager.send_json({"event": "timer_state", "state": timer.__dict__()})
            else:
                await manager.send_json(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
# endregion