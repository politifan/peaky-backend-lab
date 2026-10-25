"""Open practice checks: python check_practice.py preview.py --mode preview.

For a service: python check_practice.py app/main.py --mode persistence
Other modes: ownership, retries, service. These checks run the actual FastAPI
application. They do not award Stepik points and are not the author's hidden suite.
With --database-url use an isolated already migrated PostgreSQL database.
Without it the temporary SQLite database checks application behaviour only.
"""
import argparse
import importlib.util
import json
import sys
import tempfile
import uuid
from pathlib import Path
from contextlib import ExitStack
from fastapi.testclient import TestClient


def run(path, mode, database_url=None):
    name = 'practice_' + uuid.uuid4().hex
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    checks = []

    def record(label, passed):
        checks.append({'check': label, 'passed': bool(passed)})

    if mode == 'preview':
        with TestClient(module.app) as client:
            for title in ['x', 'я' * 80, ' учебная заявка ']:
                result = client.post('/preview', json={'title': title, 'priority': 0})
                record('valid title length ' + str(len(title)), result.status_code == 200 and result.json() == {'title': title.strip(), 'priority': 0})
            for body in [{'title': ''}, {'title': ' '}, {'title': 'x' * 81}, {'title': None}, {'title': True}, {'title': 'x', 'priority': True}, {'title': 'x', 'priority': '1'}, {'title': 'x', 'priority': 4}, {'title': 'x', 'priority': -1}, {'title': 'x', 'owner_id': 1}]:
                record('invalid body ' + json.dumps(body, ensure_ascii=False), client.post('/preview', json=body).status_code == 422)
    else:
        with tempfile.TemporaryDirectory() as folder, ExitStack() as cleanup:
            url = database_url or 'sqlite:///' + str(Path(folder) / 'practice.db').replace('\\', '/')
            secret = uuid.uuid4().hex
            app = module.create_app(url, secret, create_schema=database_url is None)
            cleanup.callback(app.state.engine.dispose)
            with TestClient(app) as client:
                tag = uuid.uuid4().hex[:12]
                users = []
                for username in ['a' + tag, 'b' + tag]:
                    created = client.post('/users', json={'username': username, 'password': 'PracticePassword42'})
                    record('register ' + username, created.status_code == 201)
                    token = client.post('/token', data={'username': username, 'password': 'PracticePassword42'})
                    record('login ' + username, token.status_code == 200)
                    users.append({'Authorization': 'Bearer ' + token.json()['access_token']})
                headers = dict(users[0], **{'Idempotency-Key': uuid.uuid4().hex})
                body = {'title': 'practice ' + tag, 'priority': 2}
                created = client.post('/tickets', json=body, headers=headers)
                record('create ticket', created.status_code == 201)
                tid = created.json()['id']
                if mode in ['ownership', 'service']:
                    record('anonymous denied', client.get('/tickets/' + str(tid)).status_code == 401)
                    record('other owner denied', client.get('/tickets/' + str(tid), headers=users[1]).status_code == 404)
                    record('other owner cannot patch', client.patch('/tickets/' + str(tid), headers=users[1], json={'title': 'changed'}).status_code == 404)
                if mode in ['retries', 'service']:
                    replay = client.post('/tickets', json=body, headers=headers)
                    record('replay preserves response', replay.status_code == 201 and replay.json() == created.json())
                    conflict = client.post('/tickets', json={'title': 'different'}, headers=headers)
                    record('same key different body rejected', conflict.status_code == 409)
                    record('one row after replay', len(client.get('/tickets', headers=users[0]).json()) == 1)
            app.state.engine.dispose()
            again = module.create_app(url, secret)
            try:
                with TestClient(again) as client:
                    saved = client.get('/tickets/' + str(tid), headers=users[0])
                    record('saved after app recreation', saved.status_code == 200 and saved.json() == created.json())
            finally:
                again.state.engine.dispose()
    return {'mode': mode, 'backend': 'PostgreSQL' if database_url else ('none' if mode == 'preview' else 'temporary SQLite'), 'checks': checks, 'passed': all(item['passed'] for item in checks), 'stepik_points_awarded': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--mode', choices=['preview', 'persistence', 'ownership', 'retries', 'service'], required=True)
    parser.add_argument('--database-url')
    args = parser.parse_args()
    try:
        result = run(args.candidate, args.mode, args.database_url)
    except Exception as error:
        result = {'passed': False, 'error': type(error).__name__ + ': ' + str(error), 'stepik_points_awarded': False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['passed'] else 1)
