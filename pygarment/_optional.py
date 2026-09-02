import importlib


class OptionalDependencyNotInstalled(ImportError):
    """Raised when an optional PyGarment capability is used without its extra."""


def require_optional(module_name, extra, feature=None, distribution_name=None, install_hint=None):
    """Import an optional module or raise an actionable installation error.

    Args:
        module_name: Python import name, for example ``cairosvg``.
        extra: PyGarment extra name, for example ``visualization``.
        feature: Optional human-readable capability that needs the module.
        distribution_name: Optional package name when it differs from module_name.
    """
    package_name = distribution_name or module_name.split(".")[0]
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        missing_name = getattr(exc, "name", None)
        if missing_name and missing_name != module_name and not module_name.startswith(f"{missing_name}."):
            raise

        capability = f" for {feature}" if feature else ""
        hint = install_hint or f"Install it with `pip install 'pygarment[{extra}]'`."
        raise OptionalDependencyNotInstalled(
            f"Optional dependency '{package_name}' is required{capability}. "
            f"{hint}"
        ) from exc
