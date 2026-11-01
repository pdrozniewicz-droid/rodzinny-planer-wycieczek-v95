import os, time, hashlib, threading
from flask import Flask, request, jsonify, make_response
import requests

app = Flask(__name__, static_folder='.', static_url_path='')
VERSION = '9.6'
USER_AGENT = os.getenv('USER_AGENT', 'RodzinnyPlanerWycieczek/9.6 (personal travel planner)')
CACHE_TTL = int(os.getenv('CACHE_TTL_SECONDS', '1800'))
# Kilka niezależnych instancji; dostępność publicznych serwerów może się zmieniać.
OVERPASS_URLS = [
    'https://overpass.private.coffee/api/interpreter',
    'https://overpass-api.de/api/interpreter',
    'https://overpass.kumi.systems/api/interpreter',
    'https://overpass.nchc.org.tw/api/interpreter',
]
cache = {}
cache_lock = threading.Lock()


def cached(key):
    now = time.time()
    with cache_lock:
        item = cache.get(key)
        if item and item[0] > now:
            return item[1]
        if item:
            cache.pop(key, None)
    return None


def cache_put(key, value, ttl=CACHE_TTL):
    with cache_lock:
        cache[key] = (time.time() + ttl, value)


def cache_key(prefix, value):
    return prefix + ':' + hashlib.sha256(value.encode('utf-8')).hexdigest()


def cors(resp):
    allowed = os.getenv('CORS_ORIGIN', '*')
    resp.headers['Access-Control-Allow-Origin'] = allowed
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Accept'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return resp


@app.after_request
def after_request(resp):
    return cors(resp)


@app.get('/')
def index():
    return app.send_static_file('index.html')


@app.get('/api/health')
def health():
    with cache_lock:
        size = len(cache)
    return jsonify(version=VERSION, cache=size, sources=['Nominatim', 'Overpass API (kilka serwerów zapasowych)', 'OSRM'], status='ok')


@app.get('/api/geocode')
def geocode():
    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify(error='Brak parametru q'), 400
    key = cache_key('geo', q.casefold())
    value = cached(key)
    if value is not None:
        return jsonify(value)
    try:
        r = requests.get('https://nominatim.openstreetmap.org/search', params={
            'q': q, 'format': 'jsonv2', 'limit': 1, 'countrycodes': 'pl'
        }, headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'}, timeout=(5, 15))
        r.raise_for_status()
        data = r.json()
        cache_put(key, data, 86400 if data else 300)
        return jsonify(data)
    except requests.RequestException as exc:
        return jsonify(error='Nie udało się pobrać geokodowania', detail=str(exc)[:300]), 502
    except ValueError:
        return jsonify(error='Nominatim zwrócił niepoprawny JSON'), 502


@app.post('/api/overpass')
def overpass():
    body = request.get_json(silent=True) or {}
    query = (body.get('query') or '').strip()
    if not query or len(query) > 30000:
        return jsonify(error='Brak zapytania lub zapytanie jest zbyt długie'), 400
    key = cache_key('osm', query)
    value = cached(key)
    if value is not None:
        return jsonify(value)

    errors = []
    # Nie ponawiamy bez końca na jednym serwerze: przechodzimy po zapasowych.
    for endpoint in OVERPASS_URLS:
        try:
            r = requests.post(
                endpoint,
                data={'data': query},
                headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'},
                timeout=(6, 22)
            )
            if r.status_code in (429, 502, 503, 504) or r.status_code >= 500:
                errors.append(f'{endpoint}: HTTP {r.status_code}')
                continue
            if r.status_code >= 400:
                errors.append(f'{endpoint}: HTTP {r.status_code}')
                continue
            try:
                data = r.json()
            except ValueError:
                errors.append(f'{endpoint}: odpowiedź nie jest poprawnym JSON-em')
                continue
            if not isinstance(data, dict) or not isinstance(data.get('elements'), list):
                errors.append(f'{endpoint}: brak listy elements w odpowiedzi')
                continue
            cache_put(key, data)
            return jsonify(data)
        except requests.Timeout:
            errors.append(f'{endpoint}: przekroczono limit czasu')
        except requests.RequestException as exc:
            errors.append(f'{endpoint}: błąd połączenia ({str(exc)[:120]})')

    return jsonify(
        error='Nie udało się pobrać danych z żadnego serwera Overpass.',
        detail=errors,
        hint='To awaria lub ograniczenie zewnętrznych źródeł danych, a nie potwierdzenie braku atrakcji. Spróbuj później lub skorzystaj z wyszukiwania awaryjnego.',
        attempted=len(OVERPASS_URLS)
    ), 502


@app.get('/api/route')
def route():
    origin = request.args.get('from', '')
    target = request.args.get('to', '')
    try:
        for pair in (origin, target):
            lon, lat = [float(x) for x in pair.split(',')]
            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                raise ValueError('poza zakresem')
    except (ValueError, TypeError):
        return jsonify(error='Parametry from/to muszą mieć format lon,lat'), 400
    key = cache_key('route', origin + ';' + target)
    value = cached(key)
    if value is not None:
        return jsonify(value)
    try:
        url = f'https://router.project-osrm.org/route/v1/driving/{origin};{target}'
        r = requests.get(url, params={'overview': 'false'}, headers={'User-Agent': USER_AGENT}, timeout=(5, 25))
        r.raise_for_status()
        data = r.json()
        cache_put(key, data, 900)
        return jsonify(data)
    except (requests.RequestException, ValueError) as exc:
        return jsonify(error='Nie udało się sprawdzić trasy', detail=str(exc)[:300]), 502


if __name__ == '__main__':
    port = int(os.getenv('PORT', '8000'))
    app.run(host='0.0.0.0', port=port, debug=False)
