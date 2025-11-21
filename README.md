# simple mirror api to send the request back to the sender

## get uv - makes python life easier
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## run
```bash
uv sync
uv run main.py
```

## from scratch
```bash
cd mirrorapi
uv sync
uv pip compile pyproject.toml -o requirements.txt
uv pip install -r requirements.txt
uv run main.py
```

## run behave tests
```bash
behave features/echo.feature
```

## Docker build
```bash
docker build -t mirrorapi .
```

## Docker run
```bash
docker run --rm -p 4500:4500 mirrorapi
```

## Docker run daemon
```bash
docker run --name mirrorapi -d -p 4500:4500 --restart unless-stopped wlanboy/mirrorapi
```

## Usage
* see swagger ui: http://127.0.0.1:4500/swagger-ui/