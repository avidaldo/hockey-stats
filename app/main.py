from __future__ import annotations

import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.service_factory import build_service
from app.ui.tk_app import HockeyApp


def main() -> None:
    service = build_service()
    app = HockeyApp(service)
    app.mainloop()


if __name__ == "__main__":
    main()
