import os


ENV_PREFIX = "FIN"
_config = None


def _load_from_env():
    global _config
    _config = {
        "DATABASE_PATH": os.getenv(f"{ENV_PREFIX}_DATABASE_PATH", "storage/fin.db"),
        "USERNAME": os.getenv(f"{ENV_PREFIX}_USERNAME", "fin"),
        "PASSWORD": os.getenv(f"{ENV_PREFIX}_PASSWORD", "fin"),
        "ENV": os.getenv(f"{ENV_PREFIX}_ENV", "dev"),
    }
    return _config

def get_config():
    if _config is None:
        _load_from_env()
    return _config
