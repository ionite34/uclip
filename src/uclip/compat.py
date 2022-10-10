import sys

__all__ = ["cached_property"]

if sys.version_info < (3, 8):  # pragma: no cover
    # noinspection PyUnresolvedReferences,PyPackageRequirements
    from backports.cached_property import cached_property
else:
    from functools import cached_property
