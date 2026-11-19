"""figkit の見本。説明ページでよく使う7種類の図を、架空の設計の例で描く。
題材は「社内で貸し出している検証用サーバーの月額費用を、月ごとに残す」設計。
    python3 example_figures.py [出力先のフォルダ]

1〜4 は、処理が1つのバッチのときの並び。5 は、処理が複数の操作のときに 2 の代わりに使う。
6 は「変更が起きたとき」、7 は「下流での動き」の節に使う。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # 図のスクリプトを別のフォルダに置くときは、figkit.py があるフォルダに変える
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
    {'title': '月ごとの費用の行と比べる', 'sources': 'server_monthly_costs, servers, sizes',
     'lines': ['行がないサーバー → 行を足す。金額は、そのときの料金表から写す', '行はあるが、月末にはもう無かったサーバー → voided_at を入れる（行は消さない）']},
])
f.save(y + 14)

# 3. 行の例と、カラムと使い道。1行目に基準の行を置き、違うセルだけに色を付ける。どのサーバーのどの月かは、行の見出しで表す
f = Fig('ex3-rows', '月ごとの費用の行の例', out)
who = lambda a, b: {'lines': [a, b], 'cls': 'plain', 'styles': ['b', 'm']}
y = f.table(38, [('どの行か', 250), ('size', 70), ('monthly_cost', 120), ('stopped', 80), ('voided_at', 180)], [
    [who('web-1 の 11月', 'ふつうに動いている。サイズ S'), D('S'), D('10,000'), D('false'), D('NULL')],
    [who('db-1 の 12月', 'サイズを上げた後'), H('L'), H('30,000'), D('false'), D('NULL')],
    [who('停止中のサーバーの 1月', '停止中も、同じ金額で数える'), D('S'), D('10,000'), H('true'), D('NULL')],
    [who('料金の改定の後にできた行', 'S の月額が 12,000 円になった'), D('S'), H('12,000'), D('false'), D('NULL')],
    [who('削除されていたサーバーの 12月', '12/20 の削除が、1/10 に登録された'), D('S'), D('10,000'), D('false'), H('1/11 2:00', '登録の次の夜のバッチ', styles=['b', 'm'])],
], pad=10)
f.legend(y + 24, 'hi', '1行目（web-1 の 11月の行）と違う所')
col = lambda s: {'lines': [s], 'cls': 'plain', 'styles': ['mono']}
y = f.table(y + 44, [('カラム', 190), ('使い道', 510)], [
    [col('server_id, month'), 'どのサーバーの、どの月の行か。この組で1行'],
    [col('size, monthly_cost'), '月末のサイズと、料金表から写した月額'],
    [col('stopped'), '月末に停止中だったか。金額には使わない'],
    [col('voided_at'), '月末には無かったと分かった日時。入っている行は合計から外す'],
], pad=10)
f.save(y + 16)

# 4. 同じ例から、月ごとの結果と合計。色は「前の月から変わった所」だけ。差の行は太字にして、色を増やさない
f = Fig('ex4-monthly', '3つの例からできる行と、月ごとの費用', out)
p = lambda v, note='', cls='box': {'lines': [v, note], 'cls': cls, 'styles': ['b', 'm']}
s = lambda v: {'lines': [v], 'cls': 'hdr', 'styles': ['b']}
y = f.table(38, [('行の monthly_cost', 148), ('10月', 138), ('11月', 138), ('12月', 138), ('1月', 138)], [
    [who('web-1', '11/10 に作成'), p('—', '行なし', 'plain'), p('10,000', '日割りしない', 'hi'), p('10,000'), p('10,000')],
    [who('db-1', '12/15 に S → L'), p('10,000'), p('10,000'), p('30,000', '月末のサイズ L', 'hi'), p('30,000')],
    [who('batch-1', '1/20 に削除'), p('10,000'), p('10,000'), p('10,000'), p('—', '月末にない', 'hi')],
    [s('費用（合計）'), s('20,000'), s('30,000'), s('50,000'), s('40,000')],
    [who('前の月との差', 'どのサーバーの分か'), p('', '', 'plain'), p('+10,000', 'web-1 の作成', 'plain'), p('+20,000', 'db-1 の変更', 'plain'), p('−10,000', 'batch-1 の削除', 'plain')],
])
f.legend(y + 24, 'hi', '前の月から変わった所')
f.note(y + 46, '金額は仮の値（S は月 10,000 円、L は月 30,000 円）')
f.save(y + 62)

# 5. 操作ごとに、読むテーブルと書くテーブル（処理が1つのバッチでないとき）。今回足す処理だけに色を付ける
f = Fig('ex5-operations', '操作ごとに、読むテーブルと書くテーブル', out)
op = lambda a, b: {'lines': [a, b], 'cls': 'plain', 'styles': ['b', 'm']}
rw = lambda *l, cls='box': {'lines': list(l), 'cls': cls}
y = f.table(38, [('操作', 170), ('読むテーブル', 200), ('書くテーブル', 330)], [
    [op('作成', '管理ツールから'), rw('sizes'), rw('servers に1行できる', 'server_events に created')],
    [op('サイズ変更', '管理ツールから'), rw('servers, sizes'), rw('servers の size を書き換える', 'server_events に resized')],
    [op('削除', '管理ツールから'), rw('servers'), rw('servers の deleted_at を入れる', 'server_events に deleted')],
    [op('月ごとの費用の記録', '毎晩 2:00 のバッチ'), rw('servers, sizes', 'server_monthly_costs', cls='hi'), rw('server_monthly_costs に行を足す', '無かったサーバーの行に voided_at を入れる', cls='hi')],
])
f.legend(y + 24, 'hi', '今回足す処理。ほかの3つは今のまま')
f.save(y + 40)

# 6. 変更が起きたとき。基準の行が無い図なので、色は「まだ決まっていない所」だけに付ける
f = Fig('ex6-exceptions', '変更が起きたとき', out)
y = f.table(38, [('起きたこと', 210), ('レコード', 270), ('結果', 220)], [
    [op('サーバーを停止した', ''), rw('行はできる', 'stopped が true になる'), rw('停止中も、同じ金額で数える')],
    [op('料金表が改定された', ''), rw('できている行は変わらない', '次にできる行から新しい金額'), rw('過去の月の費用は変わらない')],
    [op('削除が後から登録された', '3か月以内の月'), rw('行に voided_at が入る', '行は消えない'), rw('その月の合計から外れる')],
    [op('削除が後から登録された', '4か月以上前の月'), rw('行は変わらない', '見直しの範囲の外'), rw('合計に残ったままになる', '直し方は未決定', cls='bad')],
])
f.legend(y + 24, 'bad', 'まだ決まっていない所')
f.save(y + 40)

# 7. 下流での動き。テーブルから画面までを、左から右へ
f = Fig('ex7-downstream', 'テーブルから、ダッシュボードまで', out)
y = f.flow(40, [
    {'title': 'server_monthly_costs', 'lines': ['毎晩のバッチが行を足す']},
    {'title': '月ごとの合計のビュー', 'lines': ['voided_at が NULL の行を足す', '月ごとに1行']},
    {'title': '費用のダッシュボード', 'lines': ['月ごとの合計', '前の月との差']},
])
f.note(y + 24, 'ビューとダッシュボードは新しく作る。今ある画面は変えない')
f.save(y + 40)
