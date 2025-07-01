from typing import Union

from bw2data import databases


class AggregationOverride:
    """Singleton class which holds global state on overriding aggregation preferences.

    Allows for overriding with e.g. context managers."""

    def __init__(self):
        self.reset()

    def set_global_override(self, override: bool) -> None:
        if override not in {True, False, None}:
            raise ValueError(
                f"`override` value must be bool or `None`; got '{override}'"
            )
        self.global_override = override

    def set_local_overrides(self, overrides: dict[str, bool]) -> None:
        for key, value in overrides.items():
            if not key in databases:
                raise ValueError(f"Database '{key}' not found")
            if value not in {True, False}:
                raise ValueError(f"Override value must be bool; got '{value}'")
        self.local_overrides = overrides

    def reset(self):
        self.global_override = None
        self.local_overrides = {}


aggregation_override = AggregationOverride()


class AggregationContext:
    def __init__(self, override: Union[bool, dict]) -> None:
        if isinstance(override, bool) or override is None:
            aggregation_override.set_global_override(override)
        elif isinstance(override, dict):
            aggregation_override.set_local_overrides(override)
        else:
            raise ValueError("Input `override` not understood")

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        aggregation_override.reset()
