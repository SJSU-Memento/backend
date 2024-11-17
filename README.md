# Memento Backend

## Installation

### Requirements

- **Python 3.11**: Make sure you have Python 3.11 installed. You can install it with [pyenv](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation).
- **Poetry**: Install Poetry by following the instructions [here](https://python-poetry.org/docs/#installation).

### Install dependencies

```bash
poetry install
```

## Run

Before starting the backend, you'll need to run elasticsearch database and the caddy reverse proxy to server the
recorded images and frontend. Make sure you start the frontend with the proper command to make it accessible to
the dockerized caddy server. See the frontend readme. Then, run following command:

```bash
docker compose up
```

Once this is running, run the following command in another terminal window:

```bash
poetry run uvicorn app:app --reload
```
