"""Elk bestand in deze map is één Raadslid. De Koning kiest de spreekvolgorde."""
import importlib
import pkgutil


def alle():
    return [importlib.import_module(f"{__name__}.{m.name}") for m in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name)]
