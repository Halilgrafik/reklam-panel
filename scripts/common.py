import json
import os
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACCOUNTS_FILE = ROOT / "accounts" / "accounts.json"
DATA_DIR = ROOT / "data"


def load_accounts():
    with open(ACCOUNTS_FILE, encoding="utf-8") as f:
        return json.load(f)


def require_env(var_name):
    value = os.environ.get(var_name)
    if value is not None:
        value = value.strip()
    if not value:
        raise RuntimeError(
            f"Ortam degiskeni eksik: {var_name}. "
            f".env dosyana (yerelde) veya GitHub Secrets'a (Actions'ta) eklemen gerekiyor."
        )
    return value


def load_history(filename):
    path = DATA_DIR / filename
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_history(filename, history):
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def upsert_today(history, row):
    """Bugune ait satiri gunceller (ayni gun icinde birden fazla kez calisirsa
    ust uste eklemek yerine gunceller), yoksa ekler. Tarihe gore sirali tutar."""
    today = row["date"]
    history = [r for r in history if r["date"] != today]
    history.append(row)
    history.sort(key=lambda r: r["date"])
    return history


def today_str():
    return date.today().isoformat()


def now_iso():
    return datetime.now(timezone.utc).isoformat()
