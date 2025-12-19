from os import environ


def get_flask_env(key: str, default="", error=False) -> str:
    """Return the value of KEY or FLASK_KEY, otherwise, return
    a default.
    If neither is found and error is True, raise a KeyError.

    :param key: The environment variable key to look for.
    :param default: The default value to return if the key is not found.
    :param error: If True, raise a KeyError if the key is not found.
    """
    value = environ.get(key, environ.get(f"FLASK_{key}", default))
    if not value and error:
        message = f"Environment variable '{key}' not found."
        raise KeyError(message)
    return value
