# canonicalwebteam.juju-logger

A Juju logger application built with Flask.

## Installation

```bash
pip install canonicalwebteam.juju-logger
```

Or install from source:

```bash
git clone https://github.com/canonical-web-and-design/canonicalwebteam.juju-logger.git
cd canonicalwebteam.juju-logger
pip install -e .
```

### Running the application

```bash
export JUJU_DATA=~/.local/share/juju/
flask run -p 8006
```

The application will be available at `http://localhost:5000`.

### Code formatting

```bash
black .
```

## License

[LGPL](LICENSE)
# canonicalwebteam.juju-logger
