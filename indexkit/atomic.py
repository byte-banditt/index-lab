"""Publish complete directory snapshots; roll back if either rename fails.

Each directory rename is atomic. Reports/docs are a single-writer publication,
not a transaction for concurrent readers across both directories.
"""

import os
import shutil
from pathlib import Path


def publish(stage, destination):
    stage, destination = Path(stage), Path(destination)
    backups = {}
    installed = []
    try:
        for name in ("reports", "docs"):
            target = destination / name
            if target.exists():
                backup = stage / f"previous-{name}"
                os.replace(target, backup)
                backups[name] = backup
            os.replace(stage / name, target)
            installed.append(name)
    except BaseException:
        for name in reversed(installed):
            shutil.rmtree(destination / name)
        for name, backup in backups.items():
            os.replace(backup, destination / name)
        raise
    for backup in backups.values():
        shutil.rmtree(backup)
