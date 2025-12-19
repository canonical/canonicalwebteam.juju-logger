# canonicalwebteam.juju-logger

A Juju logger application built with FastAPI.


## Installation

```bash
pip install -r requirements.txt
```

### Running the application

```bash
uvicorn app:app --reload-exclude logs --reload 
```

The application will be available at `http://localhost:8000`.

## Endpoints

- `GET /environment/debug` - Retrieve debug information about the Juju environment
- `GET /environment/status` - Get the current status of the Juju environment

## License

[LGPL](LICENSE)
# canonicalwebteam.juju-logger
