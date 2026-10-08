#!/usr/bin/env python3
"""Command-line client for the live site's tool API (vpippi/assistant/api.py).

Runs the same tools as the chat assistant at /assistant/ against the production
database, so Claude Code on this PC can edit CVs and job applications without
touching the (separate) local db.sqlite3.

Config (environment variables, or a .env file in the repo root):
    SITE_API_TOKEN   required — must match ASSISTANT_API_TOKEN on the server
    SITE_API_URL     optional — defaults to https://vpippi.com

Usage:
    site_api.py tools                       list tools and their parameters
    site_api.py call TOOL [ARG ...]         run a tool
    site_api.py pending                     list staged actions awaiting confirmation
    site_api.py confirm ID | cancel ID      resolve a staged action (deletes)

Tool arguments:
    name=text          string value
    name=@path         string value read from a UTF-8 file (for long CV source / old_text / new_text)
    name:=json         non-string value, e.g.  is_default:=true   id:=3

Options for `call`:
    --field PATH       print only that field as plain text, e.g. --field output.source_content
                       (use this to read a CV's source without JSON escaping)

Examples:
    site_api.py call list_cv_variants
    site_api.py call get_cv_variant slug=apple --field output.source_content > apple.html
    site_api.py call edit_cv_content slug=apple old_text=@old.txt new_text=@new.txt
    site_api.py call update_job_application id:=7 status=Interviewing
    site_api.py call delete_cv_variant slug=apple     # only STAGES it
    site_api.py confirm 12
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_URL = 'https://vpippi.com'


def load_dotenv():
    path = Path(__file__).resolve().parent.parent / '.env'
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        os.environ.setdefault(key.strip(), value.strip().strip('"\''))


def die(message, code=1):
    print(message, file=sys.stderr)
    sys.exit(code)


def request(method, path, body=None):
    token = os.environ.get('SITE_API_TOKEN')
    if not token:
        die('SITE_API_TOKEN is not set (put it in the repo-root .env or your environment).')
    base = (os.environ.get('SITE_API_URL') or DEFAULT_URL).rstrip('/')
    data = None if body is None else json.dumps(body).encode('utf-8')
    req = urllib.request.Request(
        base + path, data=data, method=method,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            # Cloudflare in front of the site blocks urllib's default User-Agent (error 1010).
            'User-Agent': 'vpippi-site-api/1.0',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode('utf-8', 'replace')
        if exc.code == 404 and not raw.lstrip().startswith('{'):
            die(f'HTTP 404 from {base}{path}. Either the token is wrong, ASSISTANT_API_TOKEN is not set '
                'on the server (or is under 32 chars), or the server has not been updated/reloaded yet.')
        try:
            return exc.code, json.loads(raw)
        except ValueError:
            die(f'HTTP {exc.code} from {base}{path}:\n{raw[:500]}')
    except urllib.error.URLError as exc:
        die(f'Could not reach {base}: {exc.reason}')


def parse_args(items):
    args = {}
    for item in items:
        key, sep, value = item.partition('=')
        if not sep:
            die(f'Bad argument {item!r}; use name=value, name=@file or name:=json.')
        if key.endswith(':'):
            key = key[:-1]
            try:
                args[key] = json.loads(value)
            except ValueError:
                die(f'Invalid JSON for {key}: {value!r}')
            continue
        if value.startswith('@'):
            try:
                value = Path(value[1:]).read_text(encoding='utf-8')
            except OSError as exc:
                die(f'Cannot read {value[1:]}: {exc}')
        args[key] = value
    return args


def pick(data, dotted):
    for part in dotted.split('.'):
        if not isinstance(data, dict) or part not in data:
            die(f'No field {dotted!r} in response:\n{json.dumps(data, indent=2, ensure_ascii=False)}')
        data = data[part]
    return data


def emit(status, data, field=None):
    if field and status < 400:
        value = pick(data, field)
        sys.stdout.write(value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False))
        if not (isinstance(value, str) and value.endswith('\n')):
            sys.stdout.write('\n')
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    if status >= 400:
        sys.exit(1)


def main(argv):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    load_dotenv()
    if not argv or argv[0] in ('-h', '--help', 'help'):
        print(__doc__)
        return
    cmd, rest = argv[0], argv[1:]

    if cmd == 'tools':
        status, data = request('GET', '/api/tools/')
        if status >= 400:
            emit(status, data)
        for tool in data['tools']:
            props = tool['parameters'].get('properties', {})
            required = set(tool['parameters'].get('required', []))
            flag = '  [needs confirm]' if tool['requires_confirmation'] else ''
            print(f"{tool['name']}{flag}\n    {tool['description']}")
            for name, spec in props.items():
                req = '*' if name in required else ' '
                print(f"    {req} {name} ({spec['type']}): {spec['description']}")
            print()
    elif cmd == 'call':
        field = None
        if '--field' in rest:
            i = rest.index('--field')
            try:
                field = rest[i + 1]
            except IndexError:
                die('--field needs a value.')
            rest = rest[:i] + rest[i + 2:]
        if not rest:
            die('Usage: site_api.py call TOOL [name=value ...]')
        emit(*request('POST', f'/api/tools/{rest[0]}/', parse_args(rest[1:])), field=field)
    elif cmd == 'pending':
        emit(*request('GET', '/api/actions/'))
    elif cmd in ('confirm', 'cancel'):
        if len(rest) != 1 or not rest[0].isdigit():
            die(f'Usage: site_api.py {cmd} ACTION_ID')
        emit(*request('POST', f'/api/actions/{rest[0]}/{cmd}/', {}))
    else:
        die(f'Unknown command {cmd!r}. Run with --help.')


if __name__ == '__main__':
    main(sys.argv[1:])
