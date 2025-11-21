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
- uv run main.py

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
* see swagger ui: http://127.0.0.1:4500/swagger-ui/