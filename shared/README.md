# shared

アプリ横断で使う共通メモ（API連携の設定、Bubbleの小技、よく使うワークフローなど）。

## Bubble の小技

### 新しいエディタ（Property Editor Redesign）に切り替える

エディタの見た目が古い（右側のプロパティエディタが旧デザイン）ときは、プランのせいではなく、ベータ機能がオフになっているだけ。アプリごとに設定する。

1. エディタ左のメニューから **Settings → Versions** を開く
2. 下の方の **Beta Features** の一覧で、**Property Editor Redesign** にチェックを入れる
3. 必要なら **CSS ellipsis for truncated text**（はみ出したテキストを「…」で省略する機能）にもチェックを入れる

補足:

- Property Editor Redesign をオフにすると、エディタ内の Preview タブと AI Agent のピン留めも外れる
- ベータ機能は「Live で使うにはデプロイが必要」と表示されるが、エディタの見た目の切り替えはエディタ側だけの話
- 出典: 2026-10-15 古川さんに教えてもらった方法（1on1 アプリで実施）
