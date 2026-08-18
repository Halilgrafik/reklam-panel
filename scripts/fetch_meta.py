"""Meta Marketing API'den gunluk reklam verisini ceker ve data/ altina yazar.

Gerekli env var'lar (her hesap icin accounts/accounts.json'da tanimli isimlerle):
  - <ad_account_id_env>   -> "act_123456789" formatinda reklam hesabi ID'si
  - <access_token_env>    -> Sistem kullanicisi (system user) veya uzun omurlu access token
"""
import sys

import requests

from common import load_accounts, require_env, load_history, save_history, upsert_today, today_str

GRAPH_API_VERSION = "v21.0"

# Meta'nin actions[] listesindeki action_type degerleri; hesaba/kampanyaya gore
# hangisinin kullanildigi degisebilir, o yuzden birkac olasi ismi topluyoruz.
MESSAGING_ACTION_TYPES = {
    "onsite_conversion.messaging_conversation_started_7d",
    "messaging_conversation_started_7d",
}
PURCHASE_ACTION_TYPES = {
    "omni_purchase",
    "offsite_conversion.fb_pixel_purchase",
    "purchase",
}


def sum_actions(actions, wanted_types):
    if not actions:
        return 0.0
    return sum(float(a["value"]) for a in actions if a.get("action_type") in wanted_types)


def fetch_account_insights(ad_account_id, access_token):
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{ad_account_id}/insights"
    params = {
        "fields": "spend,impressions,reach,actions,action_values",
        "date_preset": "today",
        "access_token": access_token,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json().get("data", [])
    if not data:
        return {
            "spend": 0.0,
            "impressions": 0,
            "reach": 0,
            "messaging_conversations": 0,
            "purchases": 0,
            "purchase_value": 0.0,
            "results": 0,
        }
    row = data[0]
    actions = row.get("actions", [])
    action_values = row.get("action_values", [])
    return {
        "spend": float(row.get("spend", 0)),
        "impressions": int(row.get("impressions", 0)),
        "reach": int(row.get("reach", 0)),
        "messaging_conversations": int(sum_actions(actions, MESSAGING_ACTION_TYPES)),
        "purchases": int(sum_actions(actions, PURCHASE_ACTION_TYPES)),
        "purchase_value": sum_actions(action_values, PURCHASE_ACTION_TYPES),
        "results": int(sum(float(a["value"]) for a in actions)) if actions else 0,
    }


def main():
    accounts = load_accounts()
    any_error = False

    for account in accounts:
        meta_cfg = account.get("meta", {})
        if not meta_cfg.get("enabled"):
            continue

        account_id = account["id"]
        print(f"[meta] {account_id} icin veri cekiliyor...")
        try:
            ad_account_id = require_env(meta_cfg["ad_account_id_env"])
            access_token = require_env(meta_cfg["access_token_env"])
            metrics = fetch_account_insights(ad_account_id, access_token)
        except Exception as exc:
            print(f"[meta] HATA ({account_id}): {exc}", file=sys.stderr)
            any_error = True
            continue

        row = {"date": today_str(), **metrics}
        filename = f"{account_id}_meta.json"
        history = load_history(filename)
        history = upsert_today(history, row)
        save_history(filename, history)
        print(f"[meta] {account_id} kaydedildi: {row}")

    if any_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
