# reklam-panel

Meta (Facebook/Instagram) Ads ve Google Ads verilerini tek panelde gösteren,
sıfır bütçeli bir sistem. Veri saatte bir GitHub Actions ile otomatik çekilir,
sonuçlar GitHub Pages üzerinde tablo + grafik olarak gösterilir.

## Yapı

```
accounts/accounts.json     -> Hangi hesaplar takip ediliyor (SIR bilgi değil, sadece
                               "bu hesabın secret'ları hangi env var isminde" bilgisi)
scripts/common.py          -> Ortak yardımcı fonksiyonlar (env okuma, dosyaya yazma)
scripts/fetch_meta.py      -> Meta Marketing API'den veri çeker
scripts/fetch_google.py    -> Google Ads API'den veri çeker
data/                      -> Çekilen veriler buraya JSON olarak yazılır (Action commit eder)
docs/                      -> GitHub Pages'in yayınladığı statik sayfa (tablo + grafik)
.github/workflows/         -> Saatlik otomatik çalışma tanımı
.env.example               -> Yerelde test için gereken env var isimlerinin listesi (değer yok)
```

## Hesap (account) mantığı

Her reklam hesabı `accounts/accounts.json` içinde bir kayıt olarak tanımlanır.
Bu dosyada **gerçek token/secret olmaz** — sadece "bu hesabın Meta access
token'ı hangi ortam değişkeninde duruyor" gibi referanslar olur. Gerçek
değerler yalnızca `.env` (yerel) veya GitHub Secrets (Actions) içinde durur.

Yeni bir müşteri/firma eklemek istediğinde:
1. `accounts/accounts.json` içine yeni bir kayıt eklenir.
2. O hesabın token'ları için yeni env var isimleri (örn. `META_ACCESS_TOKEN_2`)
   `.env`'e veya GitHub Secrets'a eklenir.
3. Kod değişmez — script'ler `accounts.json`'daki listeyi otomatik dolaşır.

## Kurulum durumu

Bu proje adım adım kuruluyor. Şu an: proje iskeleti hazır. Sıradaki adım:
Meta ve Google Ads API erişimi için gereken bilgilerin nasıl alınacağı
(bkz. konuşma geçmişi / talimatlar).
