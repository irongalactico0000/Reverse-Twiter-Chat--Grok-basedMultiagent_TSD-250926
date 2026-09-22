"""Backward-compatible stub entrypoint — delegates to nautilus_worker. """
from __future__ import annotations

from .nautilus_worker import (  # noqa: F401
    EngineEvent,
    emit_target_cycle,
    main,
    write_events,
)

if __name__ == "__main__":
    raise SystemExit(main())
