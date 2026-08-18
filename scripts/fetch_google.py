"""Google Ads API'den gunluk reklam verisini ceker ve data/ altina yazar.

Gerekli env var'lar (her hesap icin accounts/accounts.json'da tanimli isimlerle):
  - GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET  -> Google Cloud OAuth client (tum hesaplarda ortak)
  - GOOGLE_DEVELOPER_TOKEN                   -> Google Ads developer token (tum hesaplarda ortak)
  - <refresh_token_env>                      -> Bu hesaba ozel OAuth refresh token
  - <customer_id_env>                        -> "1234567890" formatinda, tiresiz musteri no
  - <login_customer_id_env>                  -> (opsiyonel) Hesap bir MCC altindaysa, MCC musteri no
"""
import sys

import requests

from common import load_accounts, require_env, load_history, save_history, upsert_today, today_str

API_VERSION = "v18"
TOKEN_URL = "https://oauth2.googleapis.com/token"


def get_access_token(client_id, client_secret, refresh_token):
    resp = requests.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(f"Token yenileme hatasi ({resp.status_code}): {resp.text}")
    return resp.json()["access_token"]


def fetch_campaign_metrics(customer_id, access_token, developer_token, login_customer_id):
    url = f"https://googleads.googleapis.com/{API_VERSION}/customers/{customer_id}/googleAds:search"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "developer-token": developer_token,
        "Content-Type": "application/json",
    }
    if login_customer_id:
        headers["login-customer-id"] = login_customer_id

    query = """
        SELECT
          campaign.status,
          metrics.clicks,
          metrics.conversions,
          metrics.cost_micros
        FROM campaign
        WHERE segments.date DURING TODAY
    """
    resp = requests.post(url, headers=headers, json={"query": query}, timeout=30)
    resp.raise_for_status()
    results = resp.json().get("results", [])

    clicks = 0
    conversions = 0.0
    cost_micros = 0
    active_campaigns = 0
    paused_campaigns = 0

    for r in results:
        metrics = r.get("metrics", {})
        clicks += int(metrics.get("clicks", 0))
        conversions += float(metrics.get("conversions", 0))
        cost_micros += int(metrics.get("costMicros", 0))
        status = r.get("campaign", {}).get("status")
        if status == "ENABLED":
            active_campaigns += 1
        elif status == "PAUSED":
            paused_campaigns += 1

    cost = cost_micros / 1_000_000
    cpc = (cost / clicks) if clicks else 0.0

    return {
        "clicks": clicks,
        "conversions": conversions,
        "cost": cost,
        "cpc": cpc,
        "active_campaigns": active_campaigns,
        "paused_campaigns": paused_campaigns,
    }


def main():
    accounts = load_accounts()
    any_error = False

    for account in accounts:
        google_cfg = account.get("google", {})
        if not google_cfg.get("enabled"):
            continue

        account_id = account["id"]
        print(f"[google] {account_id} icin veri cekiliyor...")
        try:
            client_id = require_env(google_cfg["client_id_env"])
            client_secret = require_env(google_cfg["client_secret_env"])
            developer_token = require_env(google_cfg["developer_token_env"])
            refresh_token = require_env(google_cfg["refresh_token_env"])
            customer_id = require_env(google_cfg["customer_id_env"]).replace("-", "")
            login_customer_id_env = google_cfg.get("login_customer_id_env")
            login_customer_id = None
            if login_customer_id_env:
                import os
                login_customer_id = os.environ.get(login_customer_id_env, "").replace("-", "") or None

            access_token = get_access_token(client_id, client_secret, refresh_token)
            metrics = fetch_campaign_metrics(customer_id, access_token, developer_token, login_customer_id)
        except Exception as exc:
            print(f"[google] HATA ({account_id}): {exc}", file=sys.stderr)
            any_error = True
            continue

        row = {"date": today_str(), **metrics}
        filename = f"{account_id}_google.json"
        history = load_history(filename)
        history = upsert_today(history, row)
        save_history(filename, history)
        print(f"[google] {account_id} kaydedildi: {row}")

    if any_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
