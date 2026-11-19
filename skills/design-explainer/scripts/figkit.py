"""設計の説明ページ用の図を作る部品。SVG を HTML に書き、headless Chrome で PNG にする。

使い方（example_figures.py が動く見本）:
    from figkit import Fig
    f = Fig('r1-records', '3つの例と、今のテーブルに残るレコード')
    y = f.table(38, [('例', 170), ('サーバー', 290), ('操作の履歴', 240)], rows)   # rows は行ごとのセルのリスト
    f.note(y + 24, '金額は仮の値')
    f.save(y + 40)          # r1-records.html と r1-records.png ができる

文字数の見積もり:
    python3 figkit.py count body.md r1-records.html r2-batch.html
"""
import os, re, subprocess, sys

W = 720            # 図の幅（px）。Notion の本文幅に収まる
LH = 20            # 行送り
CSS = '''<!doctype html><html><head><meta charset="utf-8"><style>
:root{--bg:#f6f7f9;--surface:#fff;--ink:#1b2430;--muted:#5b6676;--rule:#cfd6df;--accent:#1f5f8b;--accent-soft:#e4eef6;--change:#c75a12;--change-soft:#fbeee3;--good:#2f7d4f;--good-soft:#e3f2e9;--bad:#b23a3a;--bad-soft:#f8e6e6;--warn:#8a5f00;--warn-soft:#f7efd9;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
body{margin:0;padding:12px;background:#fff}
svg text{font-family:"Hiragino Kaku Gothic ProN","Yu Gothic","Noto Sans CJK JP",sans-serif}
.box{fill:var(--surface);stroke:var(--rule);stroke-width:1.5}.hdr{fill:var(--accent-soft);stroke:var(--rule);stroke-width:1.5}.plain{fill:var(--bg);stroke:var(--rule);stroke-width:1}
.hi{fill:var(--change-soft);stroke:var(--change);stroke-width:2}.blue{fill:var(--accent-soft);stroke:var(--accent);stroke-width:1.5}.good{fill:var(--good-soft);stroke:var(--good);stroke-width:1.5}.bad{fill:var(--bad-soft);stroke:var(--bad);stroke-width:1.5}
.line{stroke:var(--muted);stroke-width:1.5;fill:none}.head{fill:var(--muted)}
.t{fill:var(--ink);font-size:15px}.b{fill:var(--ink);font-size:15px;font-weight:700}.m{fill:var(--muted);font-size:13px}.mono{fill:var(--ink);font-family:var(--mono);font-size:13px}
.up{fill:var(--good);font-size:15px;font-weight:700}.down{fill:var(--bad);font-size:15px;font-weight:700}.title{fill:var(--ink);font-size:16px;font-weight:700}
</style></head><body>'''
MARKER = '<defs><marker id="mk" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="head"/></marker></defs>'
CHROME_CANDIDATES = [
    os.environ.get('FIGKIT_CHROME', ''),
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
]


def esc(t):
    return str(t).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


class Fig:
    """1枚の図。座標は左上が原点。text/rect/arrow で描き、table/steps でよくある形をまとめて描く。"""

    def __init__(self, name, title, outdir='.'):
        self.name, self.title, self.outdir, self.parts = name, title, outdir, []
        self.text(10, 22, title, 'title')

    # ---- 基本の部品 ----
    def text(self, x, y, s, cls='t', anchor=None):
        a = f' text-anchor="{anchor}"' if anchor else ''
        self.parts.append(f'<text x="{x}" y="{y}" class="{cls}"{a}>{esc(s)}</text>')

    def rect(self, x, y, w, h, cls='box'):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" class="{cls}"/>')

    def arrow(self, d):
        """d は SVG の path（例: 'M360 100 V120'）。終点に矢印が付く。"""
        self.parts.append(f'<path d="{d}" class="line" marker-end="url(#mk)"/>')

    def note(self, y, s):
        self.text(10, y, s, 'm')

    def legend(self, y, cls, s, x=10):
        self.rect(x, y - 12, 14, 14, cls)
        self.text(x + 20, y, s, 'm')

    # ---- よくある形 ----
    def table(self, y, cols, rows, x=10, pad=12):
        """表を描いて、表の下端の y を返す。
        cols: [(見出し, 幅), ...]
        rows: 行のリスト。行はセルのリスト。セルは str か dict。
              dict のキー: lines（行ごとの文字列のリスト）、cls（box / plain / hi / good / bad / hdr）、
              styles（行ごとの文字の種類。t / b / m / mono / up / down）
        色（hi など）は「基準の行と違う所」だけに付ける。"""
        cx = x
        for name, w in cols:
            self.rect(cx, y, w, 30, 'hdr'); self.text(cx + pad, y + 20, name, 'm'); cx += w
        y += 30
        for row in rows:
            cells = [c if isinstance(c, dict) else {'lines': [c]} for c in row]
            h = 22 + LH * max(len(c['lines']) for c in cells)
            cx = x
            for (name, w), c in zip(cols, cells):
                self.rect(cx, y, w, h, c.get('cls', 'box'))
                styles = c.get('styles') or ['t'] * len(c['lines'])
                for j, s in enumerate(c['lines']):
                    self.text(cx + pad, y + 24 + j * LH, s, styles[j] if j < len(styles) else styles[-1])
                cx += w
            y += h
        return y

    def steps(self, y, items, x=10, w=700):
        """上から下へ進む処理の流れ。番号つきの箱を矢印でつなぐ。下端の y を返す。
        items: [{'title': ..., 'lines': [...], 'sources': '見るテーブル', 'cls': 'box' か 'hi'}, ...]"""
        for i, it in enumerate(items):
            lines = it.get('lines', [])
            h = 34 + LH * len(lines) + (LH + 4 if it.get('sources') else 0) + 8
            self.rect(x, y, w, h, it.get('cls', 'box')); self.rect(x, y, 44, h, 'hdr')
            self.text(x + 22, y + 28, str(i + 1), 'b', 'middle'); self.text(x + 56, y + 26, it['title'], 'b')
            for j, s in enumerate(lines):
                self.text(x + 56, y + 48 + j * LH, s, 't')
            if it.get('sources'):
                self.text(x + 56, y + 48 + len(lines) * LH + 4, '見るテーブル：' + it['sources'], 'm')
            y += h
            if i < len(items) - 1:
                self.arrow(f'M{x + w // 2} {y} V{y + 20}'); y += 22
        return y

    # ---- 保存 ----
    def save(self, height):
        """HTML と PNG を書く。height は図の高さ（最後に描いた y に 14〜20 を足した値）。"""
        os.makedirs(self.outdir, exist_ok=True)
        base = os.path.join(self.outdir, self.name)
        svg = f'<svg width="{W}" height="{height}" viewBox="0 0 {W} {height}" role="img" aria-label="{esc(self.title)}">{MARKER}{"".join(self.parts)}</svg></body></html>'
        with open(base + '.html', 'w', encoding='utf-8') as fh:
            fh.write(CSS + svg)
        chrome = next((c for c in CHROME_CANDIDATES if c and os.path.exists(c)), None)
        if not chrome:
            sys.exit('Chrome が見つかりません。環境変数 FIGKIT_CHROME に実行ファイルの場所を入れてください')
        subprocess.run([chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=2',
                        f'--window-size={W + 24},{height + 24}', f'--screenshot={os.path.abspath(base)}.png',
                        'file://' + os.path.abspath(base) + '.html'], capture_output=True, check=True)
        print(f'{self.name}.png  高さ {height}  図の中の文字 {count_chars(base + ".html")} 字')


def count_chars(path):
    """本文（.md）か図（.html）の文字数。空白、表の罫線、見出しの記号は数えない。"""
    s = open(path, encoding='utf-8').read()
    if path.endswith('.html'):
        s = ''.join(re.findall(r'<text[^>]*>([^<]*)</text>', s))
        return len(re.sub(r'\s', '', s))
    s = re.sub(r'<[^>]+>', '', s)
    return len(re.sub(r'[\s|#\-*>]', '', s))


if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == 'count':
        total = 0
        for p in sys.argv[2:]:
            n = count_chars(p); total += n; print(f'{n:6d}  {p}')
        print(f'{total:6d}  合計  （毎分 500 字で {total / 500:.1f} 分、400 字で {total / 400:.1f} 分）')
    else:
        print(__doc__)
