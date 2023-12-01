try:
    import importlib.resources as pkg_resources
except ImportError:
    import importlib_resources as pkg_resources

__version__ = pkg_resources.read_text(__name__, "VERSION").strip("\n")

from .app import run_app
