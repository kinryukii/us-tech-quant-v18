from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    """
    Resolve project root from src/qutumn/common/paths.py.
    Expected layout:
      project_root/src/qutumn/common/paths.py
    """
    return Path(__file__).resolve().parents[3]


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


ROOT = project_root()
CONFIGS_V16 = ROOT / "configs" / "v16"
STATE_V16 = ROOT / "state" / "v16"
OUTPUTS_V16 = ROOT / "outputs" / "v16"
