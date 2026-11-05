---
name: notion-memory
description: AIとやった作業の最終結果を、Notionの「AI共通メモリ」の作業ログに1件ずつ記録する／過去の記録を読み返す。「Notionに残して」「メモリに保存して」「作業ログに記録して」と言われたとき、PRを作った直後、また「前に何を決めたっけ」「過去の記録を見て」と言われたときに使う。
---

# Notion「AI共通メモリ」への記録と参照

Claude Code・Claude・ChatGPT・Gemini・Codex が共通で使う外部メモリ。途中経過は残さず、**最終的な結果だけ**を1件ずつ積み上げる。

| 名前 | 場所 |
| --- | --- |
| ルールのページ「AI共通メモリ」 | https://www.notion.so/40fe4e613e19816aa099c8ae73cdb880 |
| データベース「作業ログ」 | https://www.notion.so/d5567d242dd445d4b08ed4316f0b4e4f |
| 作業ログのデータソース | `collection://29667c75-313d-4220-bdf9-743a8b112333` |

Notionのツール（`mcp__Notion__*`）が見当たらなければ、ToolSearch で `notion` を探して読み込む。ツール名が違う環境（claude.ai のチャットなど）では、同じ役割のNotionツール（ページ作成・データベース検索）を使う。それでもNotionにつながらなければ、記録する内容をそのまま表示し、「Notionに接続できなかったので手で貼ってください」と伝える。

## 記録する（書く）

**記録するタイミング**
- PRを作った直後：何も言われなくても1件記録する。
- 「Notionに残して」などと言われたとき。
- 途中経過・試行錯誤・雑談は記録しない。

**手順**
1. このセッションの最終結果を、次の項目にまとめる。

   | 項目 | 書き方 |
   | --- | --- |
   | タイトル | 何をしたかが一目でわかる一文 |
   | 日付 | 作業した日（`TZ=Asia/Tokyo date +%F`） |
   | 対象 | Kamiculum / Hanashiru / Salonwriter / SalonAdapter Lite / HotPepper Auto Post / Joule Works / AIニュース朝刊 / AI環境・仕組み / その他 |
   | リポジトリ | 作業したGitHubリポジトリ名（例：`default_workspace`）。チャットでの作業は `なし（チャット）`。選択肢にないリポジトリは空欄にして要約に名前を書く |
   | 種類 | 成果（作った・直した）／決定（方針を決めた）／学び（次に活かすこと）／課題（残った宿題） |
   | 要約 | 3行程度。①結果 ②なぜそうしたか ③次にやること |
   | （要約に追加） | AIが何度もやり直した点・ユーザーに指摘された点があれば1行足す（毎週金曜の「週次ふりかえり」の材料になる） |
   | 記録したAI | `Claude Code` |
   | リンク | PRのURLなど（あれば） |

2. `mcp__Notion__notion-create-pages` で、`parent` を `{"type":"data_source_id","data_source_id":"29667c75-313d-4220-bdf9-743a8b112333"}` にして1件作る。properties の例：

   ```json
   {
     "タイトル": "AIニュース朝刊の配信元をボットに変更",
     "date:日付:start": "2026-11-05",
     "date:日付:is_datetime": 0,
     "対象": "AIニュース朝刊",
     "リポジトリ": "default_workspace",
     "種類": "成果",
     "要約": "配信をボット「AI News」から投稿するよう指示書を変更した。本人名義の投稿と見分けるため。次はスレッドでの質問対応の動作確認。",
     "記録したAI": "Claude Code",
     "リンク": "https://github.com/..."
   }
   ```

   ※ 「リンク」に `userDefined:` は付けない（付けるとエラーになる）。

3. 本文は基本的に空でよい。詳しい経緯を残したいときだけ箇条書きで書く。
4. パスワード・APIキー・個人情報は書かない。要約に `CLAUDE.md` のような「.」入りのファイル名を書くと、Notionが勝手にリンクにしてしまうので、「作業ルール」など言葉で言い換える。
5. 書いたら、ユーザーに「作業ログに1件残しました」とタイトルとリンクを伝える。

## 読み返す（参照）

作業を始めるときや「前に何を決めたっけ」と言われたときに使う。

1. まず `mcp__Notion__notion-query-data-sources` で、「リポジトリ」（今いるリポジトリ名）か「対象」（アプリ名・テーマ）を絞り込んで新しい順に読む。下の例の `"対象"`／`"Kamiculum"` を `"リポジトリ"`／リポジトリ名に替えればリポジトリで絞り込める。

   ```json
   {"data": {"mode": "rows",
     "data_source_url": "collection://29667c75-313d-4220-bdf9-743a8b112333",
     "filter": {"type": "group", "operator": "and", "filters": [
       {"type": "property", "property": "対象", "propertyType": "select",
        "operator": "enum_is", "value": {"type": "exact", "value": "Kamiculum"}}]},
     "sort": [{"property": "日付", "direction": "descending"}],
     "limit": 20}}
   ```

   対象をまたいでキーワードで探したいときは、`mcp__Notion__notion-search` に `data_source_url` とキーワードを渡す（作ったばかりの記録は検索に出ないことがある）。
2. 特に「決定」と「課題」は、過去の方針や積み残しなので必ず目を通す。
3. 見つかった記録と矛盾することをする場合は、先にユーザーに確認する。
