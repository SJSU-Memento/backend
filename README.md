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

```bash
poetry run uvicorn app:app --reload
```

## Database

### Setting up the database

You can quickly set up a PostgreSQL database using Docker. Run the following command to start a
PostgreSQL container:

```bash
docker compose up postgres -d
```

### Managing the database with Alembic

Whenever you make changes to the database schema, you need to create a new migration file. When
you change the app/model files, you've most likely changed the database schema. To create a new
migration file, run the following command:

```bash
poetry run alembic revision --autogenerate -m "<message>"
```

Once a revision has been created, you can apply the changes to the database by running:

```bash
poetry run alembic upgrade head
```
