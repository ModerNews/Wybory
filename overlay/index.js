const express = require('express');
const http = require('http');
const ws = require('ws');
const path = require('path');
const fs = require('fs');

const app = express();
app.use(express.static(path.resolve(__dirname, 'static')));

const server = http.createServer(app);
const wss = new ws.Server({ server, path: '/websocket' });

let currentInfoBar = [];
let currentEmblem = false;
let currentTimerState = {
  running: false,
  time: 0,
  startedAt: 0,
};
let predefOpts = fs.readFileSync(path.resolve(__dirname, 'strings.txt')).toString().split('\n');
predefOpts = predefOpts.map(str => str.trim());

let candidates = fs.readFileSync(path.resolve(__dirname, 'candidates.txt')).toString().split('\n');
candidates = candidates.map(str => str.trim());

function updateTimerState() {
  if(currentTimerState.running) {
    let current = Date.now();
    let realTime = (current - currentTimerState.startedAt) / 1000;

    currentTimerState.time = Math.max(
      currentTimerState.time - realTime, 0);

    currentTimerState.startedAt = current;
  }
}

wss.on('connection', (ws) => {
  console.log('new websocket connection');
  ws.send(JSON.stringify({
    event: 'infobar',
    content: currentInfoBar,
  }));
  ws.send(JSON.stringify({
    event: 'show_emblem',
    value: currentEmblem,
  }));
  ws.send(JSON.stringify({
    event: 'predefs',
    content: predefOpts,
  }));
  ws.send(JSON.stringify({
    event: 'candidates',
    content: candidates,
  }));

  updateTimerState();
  ws.send(JSON.stringify({
    event: 'timer_state',
    state: currentTimerState,
  }));

  ws.on('message', (data) => {
    try {
      let dat = JSON.parse(data);

      if(dat.event === 'infobar') {
        currentInfoBar = dat.content;

        wss.clients.forEach(cl => {
          cl.send(JSON.stringify({
            event: 'infobar',
            content: currentInfoBar,
          }));
        });
      }

      if(dat.event === 'show_emblem') {
        currentEmblem = dat.value;

        wss.clients.forEach(cl => {
          cl.send(JSON.stringify({
            event: 'show_emblem',
            value: currentEmblem,
          }));
        });
      }

      if(dat.event === 'show_textbar') {
        wss.clients.forEach(cl => {
          cl.send(JSON.stringify({
            event: 'show_textbar',
            type: dat.type,
            bold: dat.bold,
            text: dat.text,
          }));
        });
      }

      if(dat.event === 'update_table') {
        wss.clients.forEach(cl => {
          cl.send(JSON.stringify({
            event: 'update_table',
            group1: dat.group1,
            group2: dat.group2,
          }));
        });
      }

      if(dat.event === 'update_textbar') {
        wss.clients.forEach(cl => {
          cl.send(JSON.stringify({
            event: 'update_textbar',
            bold: dat.bold,
            text: dat.text,
          }));
        });
      }

      if(dat.event === 'hide_textbar') {
        wss.clients.forEach(cl => {
          cl.send(JSON.stringify({
            event: 'hide_textbar'
          }));
        });
      }

      if(dat.event === 'timer') {
        if(dat.type === 'start' && !currentTimerState.running) {
          currentTimerState.running = true;
          currentTimerState.startedAt = Date.now();
          wss.clients.forEach(cl => {
            cl.send(JSON.stringify({
              event: 'timer_state',
              state: currentTimerState,
            }));
          });
        }
        if(dat.type === 'stop') {
          updateTimerState();
          currentTimerState.running = false;
          wss.clients.forEach(cl => {
            cl.send(JSON.stringify({
              event: 'timer_state',
              state: currentTimerState,
            }));
          });
        }
        if(dat.type === 'set') {
          currentTimerState.running = false;
          currentTimerState.time = dat.time;

          wss.clients.forEach(cl => {
            cl.send(JSON.stringify({
              event: 'timer_state',
              state: currentTimerState,
            }));
          });
        }
      }

      if(dat.event === 'reveal_result') {
        wss.clients.forEach(cl => {
          cl.send(JSON.stringify({
            event: 'reveal_result',
            which: dat.which,
            value: dat.value,
            total: dat.total,
          }));
        });
      }
    }
    catch(error) {
      console.error(error);
    }
  });
});

server.listen(8080, '0.0.0.0');
