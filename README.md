# MirrorAPI

Eine leichtgewichtige REST-API zum Testen von HTTP-Clients und Microservices. MirrorAPI spiegelt eingehende Requests (Header, Query-Parameter, Body) zurück, simuliert HTTP-Szenarien wie beliebige Status-Codes, Verzögerungen und Fehler und kann Request/Response-Paare dauerhaft als Mocks speichern – ideal für Integrationstests, Contract-Tests und lokale Entwicklung ohne echte Backend-Abhängigkeiten.

## Was macht MirrorAPI?

MirrorAPI ist ein Entwicklungswerkzeug mit folgenden Funktionen:

### Echo-Endpoints
Sendet den eingehenden Request (Headers und Body) als Response zurück. Ideal zum Debuggen von HTTP-Clients.

### Konfigurierbare Responses
- **Status Codes**: Simuliere beliebige HTTP-Status-Codes (200, 404, 500, etc.)
- **Verzögerungen**: Füge künstliche Latenz hinzu um Timeouts zu testen
- **Fehlermeldungen**: Löse kontrollierte Fehler aus

### Request/Response Mirroring
Speichere Request/Response-Paare in einer SQLite-Datenbank. Bei späteren Requests mit identischem Body wird die gespeicherte Response zurückgegeben - perfekt für Mocking in Tests. Optional lassen sich Paare zusätzlich nach HTTP-Methode und/oder Query-Parametern disambiguieren, damit zwei "Endpunkte" mit demselben Body nicht kollidieren. Jedes Paar hat eine TTL (Standard: 1 Woche) und wird danach von Lookups ignoriert; `POST /mirror/cleanup` löscht abgelaufene Paare endgültig aus der Datenbank.

## Endpoints

| Endpoint | Beschreibung |
|----------|--------------|
| `GET /` | Info-Seite mit Link zur API-Dokumentation |
| `GET /swagger-ui` | Interaktive OpenAPI-Dokumentation |
| `GET /redoc` | Alternative API-Dokumentation (ReDoc) |
| `GET /health` | Liveness Probe |
| `GET /ready` | Readiness Probe (inkl. DB-Check) |
| `* /request/` | Echo via Header-Parameter |
| `* /echo/` | Echo via Query-Parameter |
| `* /echo/{path}` | Echo via Pfad-Parameter |
| `POST /mirror/save` | Request/Response-Paar speichern |
| `POST /mirror/delete` | Gespeichertes Paar löschen |
| `GET /mirror/list` | Alle gespeicherten (nicht abgelaufenen) Paare auflisten |
| `POST /mirror/cleanup` | Abgelaufene Paare löschen |
| `* /mirror/` | Gespeicherte Response abrufen |

`*` = GET, POST, PUT, DELETE, PATCH

## Steuerungsparameter

### Via Header (`/request/`)
```bash
curl -H "request-statuscode: 201" http://localhost:4500/request/
curl -H "request-waittime: 3" http://localhost:4500/request/
curl -H "request-errorcode: Simulated Error" http://localhost:4500/request/
```

### Via Query-Parameter (`/echo/`)
```bash
curl "http://localhost:4500/echo/?statuscode=201"
curl "http://localhost:4500/echo/?waittime=3"
curl "http://localhost:4500/echo/?errorcode=Simulated%20Error"
```

### Via Pfad (`/echo/{path}`)
```bash
curl http://localhost:4500/echo/statuscode/201
curl http://localhost:4500/echo/waittime/3
curl http://localhost:4500/echo/statuscode/201/waittime/2
```

## Installation

### UV installieren (empfohlen)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Abhängigkeiten installieren
```bash
uv lock --upgrade
uv sync
uv pip compile pyproject.toml -o requirements.txt
```

## Ausführen

### Entwicklungsmodus (mit Auto-Reload)
```bash
export DATABASE_DIR=./data
uv run uvicorn main:app --reload --host 0.0.0.0 --port 4500
```

### Produktionsmodus
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 4500
```

### Direkt starten
```bash
uv run main.py
```

## Docker

### Image bauen
```bash
docker build -t mirrorapi .
```

### Container starten
```bash
docker run --rm --name mirrorapi -p 4500:4500 \
  -v ${PWD}/data:/data \
  -e DATABASE_DIR=/data \
  mirrorapi
```

### Als Daemon starten
```bash
docker run -d --name mirrorapi -p 4500:4500 \
  -v ${PWD}/data:/data \
  -e DATABASE_DIR=/data \
  mirrorapi
```

## Tests

### Behave-Tests ausführen
```bash
uv run behave features/echo.feature
```

## Beispiele

### Request spiegeln
```bash
curl -X POST http://localhost:4500/request/ \
  -H "Content-Type: application/json" \
  -d '{"hello": "world"}'
```

Response:
```json
{
  "received_headers": {
    "content-type": "application/json",
    "host": "localhost:4500",
    ...
  },
  "received_body": {"hello": "world"}
}
```

### Mock-Response speichern
```bash
curl -X POST http://localhost:4500/mirror/save \
  -H "Content-Type: application/json" \
  -d '{
    "request": {"request_data": {"user_id": 123}},
    "response": {"response_data": {"name": "Max"}, "response_status": 200}
  }'
```

### Mock-Response abrufen
```bash
curl -X POST http://localhost:4500/mirror/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123}'
```

Response:
```json
{"name": "Max"}
```

### Gespeicherte Paare auflisten
```bash
curl http://localhost:4500/mirror/list
```

Response:
```json
[
  {
    "id": 1,
    "method": null,
    "query_params": null,
    "request_data": {"user_id": 123},
    "response_data": {"name": "Max"},
    "response_status": 200,
    "expires_at": "2026-08-07T12:00:00Z"
  }
]
```

### Paare nach Methode/Query-Parametern disambiguieren
Ohne `method`/`query_params` matcht ein gespeichertes Paar den Body unabhängig von HTTP-Methode und Query - das ist weiterhin der Standardfall. Um zwei "Endpunkte" mit identischem Body zu unterscheiden, gib beim Speichern die Methode und/oder Query-Parameter an, die beim Abruf tatsächlich verwendet werden:

```bash
curl -X POST http://localhost:4500/mirror/save \
  -H "Content-Type: application/json" \
  -d '{
    "request": {"request_data": {"user_id": 123}, "method": "GET"},
    "response": {"response_data": {"name": "Max"}, "response_status": 200}
  }'

curl -X POST http://localhost:4500/mirror/save \
  -H "Content-Type: application/json" \
  -d '{
    "request": {"request_data": {"user_id": 123}, "method": "DELETE"},
    "response": {"response_data": {"deleted": true}, "response_status": 200}
  }'
```

`GET /mirror/` mit Body `{"user_id": 123}` liefert nun `{"name": "Max"}`, `DELETE /mirror/` mit demselben Body liefert `{"deleted": true}`. Ein Paar ohne `method` dient als Fallback, falls keine speziellere Methode/Query passt. `POST /mirror/delete` löscht dabei immer alle für den Body gespeicherten Varianten auf einmal.

### TTL und Cleanup
Jedes gespeicherte Paar bekommt eine Ablaufzeit (`ttl_seconds`, Standard 604800 Sekunden = 1 Woche). Nach Ablauf wird es von `GET/POST/... /mirror/`-Lookups und `GET /mirror/list` ignoriert, bleibt aber bis zum nächsten Cleanup physisch in der SQLite-Datei.

```bash
curl -X POST http://localhost:4500/mirror/save \
  -H "Content-Type: application/json" \
  -d '{
    "request": {"request_data": {"user_id": 123}, "ttl_seconds": 3600},
    "response": {"response_data": {"name": "Max"}, "response_status": 200}
  }'

curl -X POST http://localhost:4500/mirror/cleanup
```

Response von `/mirror/cleanup`:
```json
{"deleted": 3}
```

## API-Dokumentation

Nach dem Start ist die interaktive API-Dokumentation verfügbar unter:
- Swagger UI: http://localhost:4500/swagger-ui
- ReDoc: http://localhost:4500/redoc
