"""楽天ランキングAPIが、どの形なら通るかを調べる。**見るだけ。**

商品検索は新形式（openapi.rakuten.co.jp/ichibams/...）でないと通らないことが
分かっている（guradol で実測）。ランキングも同じか、旧形式のままかを確かめる。
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

APP = os.environ.get('RAKUTEN_ICHIBA_APP_ID', '').strip()
KEY = os.environ.get('RAKUTEN_ICHIBA_ACCESS_KEY', '').strip()
AFF = os.environ.get('RAKUTEN_AFFILIATE_ID', '').strip()
SITE = os.environ.get('SITE_URL', 'https://castalert.jp').rstrip('/')

CANDIDATES = [
    ('新・Ranking 20260701', 'https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Ranking/20260701'),
    ('新・Ranking 20220601', 'https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Ranking/20220601'),
    ('新・Ranking（版なし）', 'https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Ranking'),
    ('旧・Ranking 20220601', 'https://app.rakuten.co.jp/services/api/IchibaItem/Ranking/20220601'),
    ('新・GenreSearch', 'https://openapi.rakuten.co.jp/ichibams/api/IchibaGenre/Search/20260701'),
    ('旧・GenreSearch', 'https://app.rakuten.co.jp/services/api/IchibaGenre/Search/20140222'),
]


def call(url, extra):
    params = dict(format='json', applicationId=APP, accessKey=KEY, affiliateId=AFF, **extra)
    full = f'{url}?{urllib.parse.urlencode(params)}'
    request = urllib.request.Request(full, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; castalert.jp/1.0)',
        'Referer': SITE, 'Origin': SITE,
    })
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read().decode('utf-8', 'replace'))
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode('utf-8', 'replace')[:160]
    except Exception as error:
        return 0, str(error)[:160]


def main():
    if not APP or not KEY:
        print('鍵がありません。', file=sys.stderr)
        return 1

    for label, url in CANDIDATES:
        extra = {'genreId': 0} if 'Genre' in url else {'genreId': 0, 'age': 30, 'sex': 0}
        status, payload = call(url, extra)

        if status == 200 and isinstance(payload, dict):
            keys = list(payload)[:6]
            print(f'{label}: 200  キー={keys}')
            items = payload.get('Items') or payload.get('children') or []
            for row in items[:3]:
                item = row.get('Item', row.get('child', row))
                name = str(item.get('itemName') or item.get('genreName') or '')[:44]
                print(f'    {item.get("rank", item.get("genreId", ""))}  {name}')
        else:
            print(f'{label}: {status}  {str(payload)[:120]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
