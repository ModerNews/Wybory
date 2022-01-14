import asyncio
import datetime
import json
import hashlib
import logging
import os

from logging.config import dictConfig
from typing import Optional

import uvicorn

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from Models import *


class StreamOverlay(FastAPI):
    def __init__(self):
        self.timer = TimerState()
        self.info_bar = []
        self.emblem_visible = False
        self.map_state = {"visible": False,
                     "team1": "",
                     "team2": ""}
        self.overlay_mode = "GP"

        self.teams = ["Nieznany", "Nieznany"]

        with open("strings.txt") as file:
            self.predefs = [item.strip() for item in file.read().split("\n")]

        with open("candidates.txt") as file:
            self.candidates = [item.strip() for item in file.read().split("\n")]

        super().__init__()

app = StreamOverlay()

app.mount("/static", StaticFiles(directory="../static"), name="static")
templates = Jinja2Templates(directory="../templates")


def UpdateTimer(timer_object):
    if timer_object.running:
        now = datetime.datetime.now()
        timer_val = (now - timer_object.started_at).total_seconds()

        timer_object.time = max(timer_object.time - timer_val, 0)

        timer_object.started_at = now
    return timer_object


@app.on_event('startup')
async def startup_action():
    await asyncio.sleep(2)
    os.system("explorer http://localhost:8080/start")


@app.get("/")
async def index_loader(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "team1": app.teams[0], "team2": app.teams[1]})
    # with open('../templates/index.html', encoding='utf8') as file:
    #     data = file.read()
    # return HTMLResponse(data)


@app.get("/start")
async def start_overlay(request: Request):
    return templates.TemplateResponse("start_page.html", {"request": request})



@app.get("/controller")
async def main_controller(request: Request):
    return templates.TemplateResponse("controller.html", {"request": request})
    # with open('../templates/controller.html', encoding='utf8') as file:
    #     data = file.read()
    # return HTMLResponse(data)

@app.get("/tournament")
async def tournament_view(request: Request):
    return templates.TemplateResponse('tournament-table.html', {"request": request})
    # with open('../templates/tournament-table.html', encoding='utf8') as file:
    #     data = file.read()
    # return HTMLResponse(data)


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
    await websocket.send_json({"event": "infobar", "content": app.info_bar})
    await websocket.send_json({"event": "show_emblem", "value": app.emblem_visible})
    await websocket.send_json({"event": "predefs", "content": app.predefs})
    await websocket.send_json({"event": "candidates", "content": app.candidates})
    await websocket.send_json({"event": "timer_state", "state": app.timer.__dict__()})
    await websocket.send_json({"event": "maps_state", "state": app.map_state})
    await websocket.send_json({"event": "setup_system", "mode": app.overlay_mode})
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received:\n{data}")
            if data["event"] == "timer":
                if data["type"] == "start" and not app.timer.running:
                    app.timer.running = True
                    app.timer.started_at = datetime.datetime.now()
                    data = {"event": "timer_state", "state": app.timer.__dict__()}
                elif data["type"] == "stop":
                    app.timer = UpdateTimer(app.timer)
                    app.timer.running = False
                    data = {"event": "timer_state", "state": app.timer.__dict__()}
                elif data["type"] == "set":
                    app.timer.running = False
                    app.timer.time = int(data["time"])
                    data = {"event": "timer_state", "state": app.timer.__dict__()}

            elif data['event'] == 'setup_system':
                app.overlay_mode = data['mode']
                os.system("explorer http://localhost:8080/controller")
                data = {"event": "setup_system", "mode": app.overlay_mode}

            elif data['event'] == "show_emblem":
                app.emblem_visible = data['value']
                data = {"event": "show_emblem", "value": app.emblem_visible}

            elif data['event'] == "infobar":
                app.info_bar = data['content']
                data = {"event": "infobar", "content": app.info_bar}

            elif data['event'] == "predefs":
                app.predefs = data['content']
                data = {"event": "predefs", "content": app.predefs}

            elif data['event'] == 'candidates':
                app.candidates = data['content']
                data = {"event": "candidates", "content": app.candidates}

            elif data['event'] == 'maps_state':
                app.map_state = data['state']
                data = {"event": "maps_state", "state": app.map_state}

            elif data['event'] == 'teams':
                app.teams[0] = data['team1']
                app.teams[1] = data['team2']

            print(f"Sent:\n{data}")
            await manager.send_json(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
# endregion