# simple mirror api to send the request back to the sender

## get uv - makes python life easier
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## run
```
uv sync
uv run main.py
```

### from scratch
- cd mirrorapi
- uv sync
- uv pip compile pyproject.toml -o requirements.txt
- uv pip install -r requirements.txt
- uv run main.pys

## Docker build
```
docker build -t mirrorapi .
```

## Docker run
```
docker run --rm -p 4500:4500 mirrorapi
```

## Docker run daemon
```
docker run --name mirrorapi -d -p 4500:4500 --restart unless-stopped wlanboy/mirrorapi
```

## Usage
| Scenario | Description | `curl` Command Example |
| :--- | :--- | :--- |
| **Standard Request** | A simple POST request with a JSON body. The API should respond with a `200` status code, mirroring the received body and headers. | ```bash curl -X POST http://127.0.0.1:4500/request \-H "Content-Type: application/json" \ -d '{"message": "Hello from curl!"}' ``` |
| **Statuscode (a)** | Sets the HTTP status code of the response to `201`. The API should reply with this status code while still mirroring the headers and body. | ```bash curl -i -X GET http://127.0.0.1:4500/request -H "request-statuscode: 201"``` |
| **Waittime (b)** | Adds a 5-second delay before the API responds. Useful for testing timeouts. | ```bash curl -i -X GET http://127.0.0.1:4500/request -H "request-waittime: 5" ``` |
| **Errorcode (c)** | Forces a `500` status code response with a custom error message. The API should return the error text in the body. | ```bash curl -i -X POST http://127.0.0.1:4500/request -H "request-errorcode: Invalid operation" \ -d '{"action": "delete_all"}' ``` |
| **Additional Headers** | Demonstrates how any extra headers are copied from the request to the response. The `X-Custom-Header` will appear in both the body and the response headers. | ```bash curl -i -X POST http://127.0.0.1:4500/request -H "X-Custom-Header: TestValue" -H "Content-Type: application/json" -d '{"test": "header_mirror"}' ``` |
| **Path-Based Status Code** | A GET request that sets the status code to `202` via the `/api/echo` path. | ```bash curl -i -X GET http://127.0.0.1:4500/echo/statuscode/202 ``` |
| **Path-Based Waittime** | Adds a 2-second delay via the path. | ```bash curl -i -X GET http://127.0.0.1:5000/echo/waittime/2 ``` |
| **Path-Based Error Code** | Triggers a `500` error with error message via the path. | ```bash curl -i -X GET http://127.0.0.1:4500/echo/statuscode/500/errorcode/Path-based-error ``` |
| **Combined Path Parameters** | A request that combines both status code (`204`) and waittime (`2`) in the path. | ```bash curl -i -X GET http://127.0.0.1:4500/echo/statuscode/204/waittime/2 ``` |