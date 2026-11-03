"""Worker entrypoint: discover workflows under src/workflows and run the worker."""

from __future__ import annotations

import asyncio
import os
import sys

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, os.path.abspath(os.path.join(SRC, "workflows")))
sys.path.insert(0, os.path.abspath(SRC))


async def main() -> None:
    try:
        import mistralai_workflows  # type: ignore

        if hasattr(mistralai_workflows, "discover_workflows"):
            discovered = mistralai_workflows.discover_workflows()
        else:
            from mistralai_workflows.discovery import discover_workflows  # type: ignore
            discovered = discover_workflows()
        await mistralai_workflows.run_worker(discovered)
    except ImportError:
        from mistralai.workflows.worker import discover_workflows, run_worker  # type: ignore
        discovered = discover_workflows()
        await run_worker(discovered)


if __name__ == "__main__":
    asyncio.run(main())
