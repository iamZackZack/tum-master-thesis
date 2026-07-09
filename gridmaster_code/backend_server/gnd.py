import bottle
from bottle import request, response
import json, threading, socket
from bottle import ServerAdapter
from wsgiref.simple_server import make_server, WSGIServer
from socketserver import ThreadingMixIn
import requests


def validate_movement(game_state, terrain_pieces, current_player, result):
    return {"valid": True}


def resolve_enemy_choice(game_state, terrain_pieces, initiative_order, current_player, configuration):
    return {"action": None}


def validate_targets(mode, game_state, terrain_pieces, initiative_order, player_data, current_player):
    return {"targets": []}


HOST = '::'
PORT = 5104

# ---------------- Movement store ----------------

_MOVEMENT_LOCK = threading.Lock()
_MOVEMENT_CALLBACK = None
_MOVEMENT_BUFFER = []
_MOVEMENT_BUFFER_MAX = 5


# ---------------- Helpers ----------------

def as_json(value):
    return json.loads(value) if isinstance(value, str) else value


@bottle.hook('after_request')
def _cors_hook():
    response.set_header('Access-Control-Allow-Origin', '*')
    response.set_header('Access-Control-Allow-Headers', 'Content-Type')
    response.set_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')


# ---------------- Shared state ----------------

STATE_LOCK = threading.Lock()
LAST_STATE = {
    "grid": [],
    "terrain_pieces": [],
    "character": {},
    "action_prompt": {"title": None, "message": None, "player_id": None, "actions": []},
    "target_prompt": {"title": None, "message": None, "player_id": None, "options": []}
}


# ---------------- Routes ----------------


@bottle.route('/<:re:.*>', method=['OPTIONS'])
def _options_any():
    return ''


@bottle.get('/state')
def get_state():
    with STATE_LOCK:
        data = dict(LAST_STATE)
    response.content_type = 'application/json'
    return json.dumps(data)


@bottle.post('/waitMovement')
def wait_movement():
    response.content_type = 'application/json; charset=utf-8'
    response.set_header('Cache-Control', 'no-store, max-age=0')

    cb = request.headers.get('CPEE-Callback')
    if not cb:
        response.status = 400
        return json.dumps({"error": "Missing CPEE-Callback header"})

    with _MOVEMENT_LOCK:
        global _MOVEMENT_CALLBACK
        _MOVEMENT_CALLBACK = cb
        movement = _MOVEMENT_BUFFER.pop(0) if _MOVEMENT_BUFFER else None

    if movement:
        try:
            requests.put(cb, json=movement, headers={"Content-Type": "application/json"}, timeout=10)
        except Exception:
            with _MOVEMENT_LOCK:
                _MOVEMENT_BUFFER.insert(0, movement)

    response.set_header('CPEE-CALLBACK', 'true')
    return json.dumps({"status": "waiting"})


@bottle.post('/returnMovement')
def return_movement():
    response.content_type = 'application/json; charset=utf-8'
    response.set_header('Cache-Control', 'no-store, max-age=0')

    payload = request.json or request.forms

    pos = payload.get('position')
    movement = {
        "position": [int(pos[0]), int(pos[1])],
        "timestamp": payload.get('timestamp')
    }

    with _MOVEMENT_LOCK:
        global _MOVEMENT_CALLBACK
        cb = _MOVEMENT_CALLBACK

    if cb:
        try:
            r = requests.put(cb, json=movement, headers={"Content-Type": "application/json"}, timeout=10)
            r.raise_for_status()
        except Exception as e:
            response.status = 502
            return json.dumps({"error": "callback failed", "detail": str(e)})
        finally:
            with _MOVEMENT_LOCK:
                if _MOVEMENT_CALLBACK == cb:
                    _MOVEMENT_CALLBACK = None
        return json.dumps({"status": "forwarded"})

    with _MOVEMENT_LOCK:
        _MOVEMENT_BUFFER.append(movement)
        if len(_MOVEMENT_BUFFER) > _MOVEMENT_BUFFER_MAX:
            _MOVEMENT_BUFFER.pop(0)

    return json.dumps({"status": "buffered"})


@bottle.post('/visualizeGrid')
def visualize_grid():
    response.content_type = 'application/json; charset=utf-8'
    response.set_header('Cache-Control', 'no-store, max-age=0')

    payload = request.json or request.forms
    game = as_json(payload.get('game'))
    terrains = as_json(payload.get('terrains') or payload.get('terrain_pieces'))

    with STATE_LOCK:
        LAST_STATE["grid"] = game or []
        LAST_STATE["terrain_pieces"] = terrains or []

    return json.dumps({"status": "ok"})


@bottle.post('/visualizeStats')
def visualize_stats():
    response.content_type = 'application/json; charset=utf-8'
    response.set_header('Cache-Control', 'no-store, max-age=0')

    payload = request.json or request.forms
    character = as_json(payload.get('character'))

    with STATE_LOCK:
        LAST_STATE["character"] = character or {}

    return json.dumps({"status": "ok"})


@bottle.post('/visualizeAction')
def visualize_action():
    response.content_type = 'application/json; charset=utf-8'
    response.set_header('Cache-Control', 'no-store, max-age=0')

    payload = request.json or request.forms

    with STATE_LOCK:
        LAST_STATE["action_prompt"] = {
            "title": payload.get('title') or payload.get('t'),
            "message": payload.get('message') or payload.get('msg'),
            "player_id": payload.get('player_id') or payload.get('pid'),
            "actions": as_json(payload.get('actions')) or []
        }

    return json.dumps({"status": "ok"})


@bottle.post('/visualizeTargets')
def visualize_targets():
    response.content_type = 'application/json; charset=utf-8'
    response.set_header('Cache-Control', 'no-store, max-age=0')

    payload = request.json or request.forms

    with STATE_LOCK:
        LAST_STATE["target_prompt"] = {
            "title": payload.get('title') or payload.get('t'),
            "message": payload.get('message') or payload.get('msg'),
            "player_id": payload.get('player_id') or payload.get('pid'),
            "options": as_json(payload.get('options')) or []
        }

    return json.dumps({"status": "ok"})


@bottle.post('/validateMovement')
def validate_movement_route():
    response.content_type = 'application/json; charset=utf-8'
    response.set_header('Cache-Control', 'no-store, max-age=0')

    payload = request.json or request.forms
    out = validate_movement(
        game_state=as_json(payload.get('game_state')),
        terrain_pieces=as_json(payload.get('terrain_pieces')),
        current_player=as_json(payload.get('current_player')),
        result=as_json(payload.get('result'))
    )
    return json.dumps(out)


@bottle.post('/enemyChoice')
def enemy_choice_route():
    response.content_type = 'application/json; charset=utf-8'
    response.set_header('Cache-Control', 'no-store, max-age=0')

    payload = request.json or request.forms
    out = resolve_enemy_choice(
        game_state=as_json(payload.get('game_state')),
        terrain_pieces=as_json(payload.get('terrain_pieces')),
        initiative_order=as_json(payload.get('initiative_order')),
        current_player=as_json(payload.get('current_player')),
        configuration=as_json(payload.get('configuration'))
    )
    return json.dumps(out)


@bottle.post('/validateTargets')
def validate_targets_route():
    response.content_type = 'application/json; charset=utf-8'
    response.set_header('Cache-Control', 'no-store, max-age=0')

    payload = request.json or request.forms
    out = validate_targets(
        mode=payload.get('mode'),
        game_state=as_json(payload.get('game_state')),
        terrain_pieces=as_json(payload.get('terrain_pieces')),
        initiative_order=as_json(payload.get('initiative_order')),
        player_data=as_json(payload.get('player_data')) or [],
        current_player=as_json(payload.get('current_player'))
    )
    return json.dumps(out)


# ---------------- Main ----------------

class ThreadingWSGIServerIPv6(ThreadingMixIn, WSGIServer):
    address_family = socket.AF_INET6
    daemon_threads = True


class ThreadedServer(ServerAdapter):
    def run(self, handler):
        httpd = make_server(self.host, self.port, handler, server_class=ThreadingWSGIServerIPv6)
        print(f"Threaded server (IPv6) listening on [{self.host}]:{self.port}")
        httpd.serve_forever()


if __name__ == '__main__':
    bottle.debug(True)
    bottle.run(host=HOST, port=PORT, server=ThreadedServer)
