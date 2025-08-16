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
| **Standard Request** | A simple POST request with a JSON body. The API should respond with a `200` status code, mirroring the received body and headers. | ```bash<br>curl -X POST [http://127.0.0.1:4500/request](http://127.0.0.1:4500/request) \ <br> -H "Content-Type: application/json" \ <br> -d '{"message": "Hello from curl!"}'<br>``` |
| **Statuscode (a)** | Sets the HTTP status code of the response to `201`. The API should reply with this status code while still mirroring the headers and body. | ```bash<br>curl -i -X GET [http://127.0.0.1:4500/request](http://127.0.0.1:4500/request) \ <br> -H "request-statuscode: 201"<br>``` |
| **Waittime (b)** | Adds a 5-second delay before the API responds. Useful for testing timeouts. | ```bash<br>curl -i -X GET [http://127.0.0.1:4500/request](http://127.0.0.1:4500/request) \ <br> -H "request-waittime: 5"<br>``` |
| **Errorcode (c)** | Forces a `500` status code response with a custom error message. The API should return the error text in the body. | ```bash<br>curl -i -X POST [http://127.0.0.1:4500/request](http://127.0.0.1:4500/request) \ <br> -H "request-errorcode: Invalid operation" \ <br> -d '{"action": "delete_all"}'<br>``` |
| **Additional Headers** | Demonstrates how any extra headers are copied from the request to the response. The `X-Custom-Header` will appear in both the body and the response headers. | ```bash<br>curl -i -X POST [http://127.0.0.1:4500/request](http://127.0.0.1:4500/request) \ <br> -H "X-Custom-Header: TestValue" \ <br> -H "Content-Type: application/json" \ <br> -d '{"test": "header_mirror"}'<br>``` |

