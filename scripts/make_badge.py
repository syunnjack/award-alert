"""ランキングで取った順位を、商品ページに貼れる画像にする。

## なぜ画像なのか

楽天もYahooも、商品ページに置けるのは画像とHTMLだけ。
「デイリーランキング1位」を文字で書いても、**取った証拠にはならない。**
順位・ジャンル・いつの話かを1枚に入れて、そのまま貼れる形にする。

## 嘘を書かせない作り

**いつの順位かを必ず入れる。** 期間の無い「1位」は、いつまでも1位のように
読めてしまう。景品表示法の有利誤認になりうるので、日付は消せない項目にする。

**ジャンル名も必ず入れる。** 「1位」だけだと総合1位に見える。
小さなジャンルの1位を総合1位のように見せるのは、優良誤認にあたる。

だから `make_badge()` は rank / genre / date が揃わないと作らない。

## 使い方

    python scripts/make_badge.py --rank 1 --genre "財布・ケース" \\
        --mall rakuten --date 2026-09-03 --out dist/badge.png

環境変数:
  BADGE_FONT      使うフォント（既定は環境から自動で探す）
"""
import argparse
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent

# 日本語が出るフォント。上から順に探す。
# GitHub Actions（ubuntu）では fonts-noto-cjk を入れると下の2つが出る。
FONT_CANDIDATES = [
    os.environ.get('BADGE_FONT', ''),
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
    '/usr/share/fonts/truetype/fonts-japanese-gothic.ttf',
    r'C:\Windows\Fonts\YuGothB.ttc',
    r'C:\Windows\Fonts\meiryob.ttc',
    r'C:\Windows\Fonts\msgothic.ttc',
]

MALL_LABEL = {
    'rakuten': '楽天市場',
    'yahoo': 'Yahoo!ショッピング',
}

# モールごとの色。**それぞれのブランド色は使わない。**
# 公式の受賞バナーと見間違えられると、こちらが作ったものだと分からなくなる。
THEME = {
    1: ('#b8860b', '#fff8e1', '#7a5b06'),
    2: ('#7d868f', '#f4f6f8', '#4c545c'),
    3: ('#a06a3c', '#fbf3ec', '#6d4626'),
}
DEFAULT_THEME = ('#2b4d7e', '#f2f5fa', '#1b3557')


def find_font():
    for path in FONT_CANDIDATES:
        if path and Path(path).exists():
            return path
    return ''


def font_at(path, size):
    return ImageFont.truetype(path, size)


def fit(draw, text, path, start, max_width):
    """入る大きさまで縮める。**溢れさせない。**"""
    size = start
    while size > 10:
        font = font_at(path, size)
        if draw.textlength(text, font=font) <= max_width:
            return font
        size -= 2
    return font_at(path, 10)


def jp_date(iso):
    year, month, day = iso.split('-')
    return f'{int(year)}年{int(month)}月{int(day)}日'


def make_badge(rank, genre, mall, day, out_path, width=600, height=340):
    """**rank / genre / date が揃わないと作らない。**

    「1位」だけの画像は、いつの・どのジャンルの1位か分からない。
    総合1位のように読まれると優良誤認になる。作れないことにして防ぐ。
    """
    if not rank or not genre or not day:
        raise ValueError('順位・ジャンル・日付の3つが揃わないと画像は作りません。')

    font_path = find_font()
    if not font_path:
        raise RuntimeError('日本語のフォントが見つかりません。BADGE_FONT で指定してください。')

    accent, back, deep = THEME.get(rank, DEFAULT_THEME)

    image = Image.new('RGB', (width, height), back)
    draw = ImageDraw.Draw(image)

    draw.rectangle([0, 0, width - 1, height - 1], outline=accent, width=3)
    draw.rectangle([10, 10, width - 11, height - 11], outline=accent, width=1)

    pad = 34
    inner = width - pad * 2

    mall_name = MALL_LABEL.get(mall, mall)
    mall_font = fit(draw, mall_name, font_path, 24, inner)
    draw.text((width / 2, 44), mall_name, font=mall_font, fill=deep, anchor='mm')

    genre_text = f'{genre} ランキング'
    genre_font = fit(draw, genre_text, font_path, 30, inner)
    draw.text((width / 2, 92), genre_text, font=genre_font, fill=deep, anchor='mm')

    rank_text = f'{rank}'
    rank_font = fit(draw, rank_text, font_path, 130, inner * 0.5)
    unit_font = font_at(font_path, 46)

    rank_width = draw.textlength(rank_text, font=rank_font)
    unit_width = draw.textlength('位', font=unit_font)
    left = (width - (rank_width + unit_width + 8)) / 2

    draw.text((left, 196), rank_text, font=rank_font, fill=accent, anchor='ls')
    draw.text((left + rank_width + 8, 194), '位', font=unit_font, fill=accent, anchor='ls')

    # **日付は消せない。** いつの順位か分からない「1位」は誤解を招く。
    day_text = f'{jp_date(day)} 時点'
    day_font = fit(draw, day_text, font_path, 22, inner)
    draw.text((width / 2, height - 58), day_text, font=day_font, fill=deep, anchor='mm')

    note_font = font_at(font_path, 15)
    draw.text((width / 2, height - 30), 'このジャンル内の順位です', font=note_font,
              fill='#6b7280', anchor='mm')

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out, 'PNG')
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rank', type=int, required=True)
    parser.add_argument('--genre', required=True)
    parser.add_argument('--mall', default='rakuten')
    parser.add_argument('--date', required=True)
    parser.add_argument('--out', default='dist/badge.png')
    args = parser.parse_args()

    try:
        path = make_badge(args.rank, args.genre, args.mall, args.date, args.out)
    except (ValueError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 1

    print(f'{path} を作りました。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
