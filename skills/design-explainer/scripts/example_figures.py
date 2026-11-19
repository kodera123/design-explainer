"""figkit の見本。説明ページでよく使う4つの形を、架空の設計の例で描く。
題材は「社内で貸し出している検証用サーバーの月額費用を、月ごとに残す」設計。
    python3 example_figures.py [出力先のフォルダ]
"""
import sys
from figkit import Fig

out = sys.argv[1] if len(sys.argv) > 1 else '.'
H = lambda *lines, cls='hi', styles=None: {'lines': list(lines), 'cls': cls, 'styles': styles or ['b']}   # 基準と違うセル
D = lambda s: {'lines': [s], 'styles': ['m']}                                                               # 基準と同じセル

# 1. 代表的な例ごとに、今のテーブルに残るレコード
f = Fig('ex1-records', '3つの例と、今のテーブルに残るレコード', out)
label = lambda *l: {'lines': list(l), 'cls': 'plain', 'styles': ['b', 'b', 'm', 'm']}
ev = lambda *l: {'lines': list(l), 'styles': ['mono' if s.isascii() else 'm' for s in l]}
y = f.table(38, [('例', 170), ('サーバー servers', 290), ('操作の履歴 server_events', 240)], [
    [label('web-1', '作って使い続ける', '11/10 に作成'), {'lines': ['作成で1行できる', 'size は S']}, ev('created', '日付 11/10')],
    [label('db-1', 'サイズを上げる', '12/15 に S → L'), {'lines': ['同じ行の size を', 'S から L に書き換える']}, ev('resized', '日付 12/15')],
    [label('batch-1', '削除する', '1/20 に削除'), {'lines': ['同じ行に deleted_at が入る', '行は消えない']}, ev('deleted', '日付 1/20')],
])
f.text(10, y + 24, 'サーバーは今のサイズだけ、履歴はサイズも金額も持たない → 過去の月の費用はどちらにも残らない', 'b')
f.save(y + 40)

# 2. 1回の処理の流れ（見るテーブルを添える）
f = Fig('ex2-batch', '毎晩 2:00 のバッチが、1回の実行ですること', out)
y = f.steps(40, [
    {'title': '対象の月を決める', 'lines': ['前月の行がまだなければ作る。直近3か月の行は、毎晩見直す']},
    {'title': 'その月の月末にあったサーバーを選ぶ', 'lines': ['月末の日の終わりに、削除されていないサーバー。停止中も含む'], 'sources': 'servers.created_at, deleted_at'},
    {'title': '月ごとの費用の行と比べる', 'cls': 'hi', 'sources': 'server_monthly_costs, sizes.monthly_price',
     'lines': ['行がないサーバー → 行を足す。金額は、そのときの料金表から写す', '行はあるが、月末にはもう無かったサーバー → voided_at を入れる（行は消さない）']},
])
f.save(y + 14)

# 3. 行の例。1行目に基準の行を置き、違うセルだけに色を付ける
f = Fig('ex3-rows', '月ごとの費用の行の例', out)
who = lambda a, b: {'lines': [a, b], 'cls': 'plain', 'styles': ['b', 'm']}
y = f.table(38, [('どの行か', 250), ('size', 70), ('monthly_cost', 120), ('stopped', 80), ('voided_at', 180)], [
    [who('ふつうに動いているサーバー', 'サイズ S、料金の改定の前'), D('S'), D('10,000'), D('false'), D('NULL')],
    [who('db-1 の 12月', 'サイズを上げた後'), H('L'), H('30,000'), D('false'), D('NULL')],
    [who('停止中のサーバーの 1月', '停止中も、同じ金額で数える'), D('S'), D('10,000'), H('true'), D('NULL')],
    [who('料金の改定の後にできた行', 'S の月額が 12,000 円になった'), D('S'), H('12,000'), D('false'), D('NULL')],
    [who('削除されていたサーバーの 12月', '12/20 の削除が、1/10 に登録された'), D('S'), D('10,000'), D('false'), H('1/11 2:00', '登録の次の夜のバッチ', styles=['b', 'm'])],
], pad=10)
f.legend(y + 24, 'hi', '1行目（ふつうに動いているサーバーの行）と違う所')
f.save(y + 40)

# 4. 同じ例から、月ごとの結果と合計
f = Fig('ex4-monthly', '3つの例からできる行と、月ごとの費用', out)
p = lambda v, note='', cls='box': {'lines': [v, note], 'cls': cls, 'styles': ['b', 'm']}
s = lambda v: {'lines': [v], 'cls': 'hdr', 'styles': ['b']}
y = f.table(38, [('行の monthly_cost', 148), ('10月', 138), ('11月', 138), ('12月', 138), ('1月', 138)], [
    [who('web-1', '11/10 に作成'), p('—', '行なし', 'plain'), p('10,000', '日割りしない'), p('10,000'), p('10,000')],
    [who('db-1', '12/15 に S → L'), p('10,000'), p('10,000'), p('30,000', '月末のサイズ L', 'good'), p('30,000')],
    [who('batch-1', '1/20 に削除'), p('10,000'), p('10,000'), p('10,000'), p('—', '月末にない', 'plain')],
    [s('費用（合計）'), s('20,000'), s('30,000'), s('50,000'), s('40,000')],
    [who('前の月との差', 'どのサーバーの分か'), p('', '', 'plain'), {'lines': ['+10,000', 'web-1 の作成'], 'cls': 'plain', 'styles': ['up', 'm']},
     {'lines': ['+20,000', 'db-1 の変更'], 'cls': 'plain', 'styles': ['up', 'm']}, {'lines': ['−10,000', 'batch-1 の削除'], 'cls': 'plain', 'styles': ['down', 'm']}],
])
f.legend(y + 24, 'good', '前の月の行と金額が違う所')
f.note(y + 46, '金額は仮の値（S は月 10,000 円、L は月 30,000 円）')
f.save(y + 62)
