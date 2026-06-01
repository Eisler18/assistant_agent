from datetime import UTC, datetime, timedelta
from pathlib import Path
import shutil

from assistant_agent.repository.json_repository import JsonRepository

from .fixtures.seed_template import write_seed

def setup_repository(seed_path: Path, tmp_dir: Path) -> JsonRepository:
  tmp_dir.mkdir(parents=True, exist_ok=True)
  target_path = tmp_dir / seed_path.name
  shutil.copyfile(seed_path, target_path)
  return JsonRepository(root_path=tmp_dir, file_name=seed_path.name)

def ensure_seed(seed_path: Path) -> None:
  if not seed_path.exists():
    write_seed(seed_path)
    return

  seed_age = datetime.now(UTC) - datetime.fromtimestamp(seed_path.stat().st_mtime, UTC)
  if seed_age > timedelta(hours=1):
    write_seed(seed_path)
