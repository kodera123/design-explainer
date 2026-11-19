# Notion に載せて、画面で確かめる

ツールの名前は Notion の MCP サーバーのもの。ブラウザは、画面のスクリーンショットが撮れるものなら何でもよい。

## 図を載せる

1. `notion-create-file-upload` を図1枚につき1回呼ぶ（`filename` に PNG の名前）。
2. 返ってきた `upload_url` に、`upload_headers` のヘッダーをすべて付けて、ファイルを multipart で POST する。
   ```bash
   curl -s -X POST "<upload_url>" -H "authorization: Bearer <返ってきた値>" -F "file=@r1-records.png;type=image/png"
   ```
   返ってきたヘッダーが複数あれば、`-H` を増やす。アップロードの URL は短い時間（10 分ほど）で切れる。図が確定してから作る。
3. アップロードの応答にある `suggested_markdown` を、本文の図を置きたい所に、前後に空行を入れて置く。形は `<image source="file-upload://<file_upload_id>">図の題</image>`。

## ページを作る・直す

- 新しく作るときは `notion-create-pages`。置き場所はユーザーに確かめる。
- 節を入れ替えるときは `notion-update-page` の `replace_content` が確実。**すでに載っている図は、取得した本文にある `notion-file-block://…` の source をそのまま書けば残る**（アップロードし直さなくてよい）。子ページや DB のタグも、取得したとおりに残す。
- コメントが付いた段落は書き換えない。前後に足す。
- ほかのページへのリンクは `<mention url="…"/>`、PR は markdown のリンクにする。人へのメンションは通知が飛ぶので、頼まれていなければ付けない。
- `servers.id` のように「語.語」の形は、URL として自動でリンクになる。「servers の id」と書く。

## 画面で見る

markdown を取得し直しても、見た目は分からない。ブラウザを操作するツール（Claude in Chrome など）でページを開き、上から下までスクリーンショットで見る。

- 図がすべて表示されているか。折りたたみの中も1つ開いて見る
- 節が1画面〜1画面半に収まっているか。1つだけ長い節がないか
- 素の表のセルで、文字が途中で折り返していないか。表が本文の幅からはみ出していないか
- 図と図の間に、文が3文を超えて続いていないか

開いたタブは、見終わったら閉じる。
