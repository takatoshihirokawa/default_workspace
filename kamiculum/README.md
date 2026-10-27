# Kamiculum

- Bubble appname: `mendokusai`（Growthプラン / ブランチ最大10）
- エディタ: https://bubble.io/page?id=mendokusai
- 本番: https://app.kamiculum.com
- LP: https://kamiculum.com/lp/page

最終調査日: 2026-10-27（Mainブランチを読み取りで調査）

## 概要

美容室向けの教育・フィードバックプラットフォーム。動画やテキストの教材でスタッフを教育し、進捗管理とメンターからのフィードバックを一元化する。

- 料金: 法人単位の定額 月額20,000円（税別）。人数・店舗数は無制限
- 今後の予定: 外部カリキュラムの購入機能（カテゴリに販売価格などの項目が用意済み）

## ユーザーと権限

| 区分 | Option Set | 値 |
| --- | --- | --- |
| 運営/利用者 | `OP_user_type` | サービスオーナー（運営側・全データ閲覧）/ 一般ユーザー |
| 管理権限 | `OP_is_manager`（User `management_role`） | マネージャー / 一般スタッフ |
| 役割 | `OP_role` | アシスタント（学習者）/ スタイリスト（メンター） |
| 公開範囲 | `OP_access_level` | カリキュラム・カテゴリ・フォルダ・進捗に付与 |

- 所属の階層: Company（法人）→ salon（店舗）→ User
- ほぼ全データが `company` を持ち、法人単位でデータを分けている
- 学習者は User の `mentors` に担当メンターのリストを持つ

## データ設計

| データタイプ（key） | 表示名 | 内容 |
| --- | --- | --- |
| `company` | Company | Stripe契約、請求サイクル、オプションプラン、日報閲覧範囲、紹介元代理店 |
| `salon` | salon | 店舗 |
| `curriculum_domain` | CurriculumFolder | 教材の第1階層 |
| `curriculum_group` | CurriculumCategory | 教材の第2階層。販売価格・販売状況・販売元を持つ |
| `curriculum` | Curriculum | 教材。動画（Cloudflare Stream）、画像、テキスト、目安日数 |
| `progress` | Records | 学習者×カリキュラムの進捗。担当メンター、未読管理、予定日/実績日 |
| `feedback` | Feedback | 進捗に紐づく提出（動画・画像・本文） |
| `share_comment1` | MentorNote | メンターから学習者へのメモ |
| `feedpost` / `feedmedia` / `feedcomment` | Feed系 | 日報・相談のフィード（リアクション、有効期限つき） |
| `notification` | Notification | 通知履歴。recipient / title / message / url / type / status |
| `invite` / `invite_validation` | Invite | スタッフ招待と検証 |
| `play_session` | PlaySession | 動画の視聴記録 |
| `user_monthly_stats` | UserMonthlyStats | 月別の学習量集計 |
| `lineincomingmessage` | LineIncomingMessage | LINEで受け取ったメッセージ |
| `agency1` ほか | Pertners / Commission系 / SalesRecords / StripePrice / OptionPlan | 代理店と手数料、課金 |

## ページ構成

- 認証: `index`（ログイン）、`signup`、`signup_invite`、`forgotpw`、`reset_pw`
- 学習者: `curriculum_list`（ログイン後の起点）、`curriculum_detail`、`progress`、`progress_detail`、`feedback`、`feed`、`mypage`
- マネージャー・メンター: `progress_list`、`progress_overview`、`progress_analytics`、`manage_staff`、`manage_salon`、`manage_curriculum_list` / `_detail` / `_draft`、`manage_folder`、`manage_category`、`csv`
- 課金: `billing`、`plans`、`thanks`、`expired`、`canceled`
- 運営・代理店: `dashboard`、`commissions`、`commission_statement_detail`
- その他: `policy`、`terms`、`low`、`404`、`test`
- 共通の再利用エレメント: `Header`（全ページ上部、スマホ・PCとも表示）、`SideBar`、`footer`、`sp_footer`
- モバイル用ビュー: `Home`、`update_app`

## 外部連携とバックエンドワークフロー

| 連携先 | 主なワークフロー |
| --- | --- |
| Stripe | `stripe_create_account`、`stripe_payment_succeeded` / `_failed`、`stripe_subscription_update` / `_deleted`（支払い成功時に売上・手数料の記録まで実行） |
| LINE | `line_webhook`（受信→Slack転送）、`notify_mentors_*`、`send_feedback_*`。ログインは「LINE LOGIN aggressive」 |
| Slack | `slack_interactivity`、`slack_to_pdf` |
| Cloudflare Stream | 動画アップロード系、`stream_ready` / `_fb` / `_feed` |
| SelectPDF | `send_pdf`、`schedule_pdf`、`send_pdf (admin)` |
| Progressier | プラグイン導入済み・未使用（プッシュ通知で使う予定） |

その他: 招待の検証（`validate_invite_*`）、フィードのメディア管理、定期処理（`run_weekly_delete_short_play_sessions`）、再計算（`recalculate_*`）

### 通知の仕組み（LINE）

Notification を1件作り、続けてLINEに送る。Notification はバックエンドのワークフローとページ内のワークフローの両方で作られている。

#### 通知の種類（`OP_Notification_type`）

| type | 内容 |
| --- | --- |
| `feedback_message` | カリキュラムへのコメント（メンター→学習者、学習者→メンターの両方向） |
| `feed_post_comment` | 自分のフィード投稿へのコメント |
| `mentee_curriculum_started` | メンティーがカリキュラムを開始 |
| `mentee_video_completed` | メンティーが動画の視聴を完了 |
| `mentee_curriculum_completed` | メンティーがカリキュラムを完了 |
| `curriculum_completed_by_mentor` | メンターがカリキュラムを完了にした |

#### ページごとの通知の発生元

**curriculum_detail（学習者側）**

| 操作 | 呼んでいるもの | 届く相手 |
| --- | --- | --- |
| フィードバック送信（テキスト・画像・動画） | `send_feedback_comment_notification_to_mentor` | メンター |
| カリキュラム開始 | `notify_mentors_curriculum_started` | メンター |
| カリキュラム完了 | `notify_mentors_curriculum_completed` | メンター |
| 動画の視聴完了 | `notify_mentors_video_completed` | メンター |
| 「視聴完了」ボタン | `send_feedback_message_notification_to_learner` | 学習者（※要確認: 学習者が自分の操作の通知を受け取っている可能性） |

**progress_detail（メンター側）**

| 操作 | 呼んでいるもの | 届く相手 |
| --- | --- | --- |
| テキストでフィードバック | `send_feedback_message_notification_to_learner` | 学習者 |
| 画像・動画でフィードバック | `send_feedback_media_notification_to_learner` | 学習者 |
| メンターが完了にする | ページ内で Notification を直接作成 | 学習者 |

**feed**

| 操作 | 呼んでいるもの | 届く相手 |
| --- | --- | --- |
| コメント送信（PC: `create_comment_pc` / スマホ: `create_comment_sp`） | ページ内で Notification を直接作成 | 投稿者 |

#### 補足

- `send_feedback_comment_notification_to_mentor` の条件: メンターの `notification_types` に feedback_message を含む、`line_id` が空でない、本文あり（画像用・動画用は別アクション）
- タイトル例: 「○○さんから「カリキュラム名」にメッセージが届いています。」（50文字を超えることがある）
- プッシュ通知はデータトリガー（Notification 作成時）1つで、上記すべての発生元を拾える。既存のワークフローは変更不要
- 画像・動画のフィードバック（`send_feedback_media_notification_to_learner` など）は本文が空になる可能性が高く、プッシュでは固定文に切り替える分岐が必要

## 気になる点・リスク

1. **プライバシールールの穴（優先度: 高）**: Notification、FeedPost、Invite、MentorNote、salon、CurriculumFolder、Pertners（代理店の手数料率・連絡先）が「everyone: 全項目閲覧・検索可」。他法人や未ログインの人から読める可能性がある
2. **Company が誰からも見えない設定**: 「everyone: 閲覧不可」のみ。画面に法人情報を出している箇所があれば要確認
3. **認証なしの公開API**: `line_webhook`、`stripe_payment_succeeded` が公開かつプライバシールール無視。送信元の署名検証の有無は未確認
4. **中身が空の公開API**: `slack_interactivity`
5. **本番で開ける `test` ページ**: mypage設定画面のコピー
6. **未使用の可能性**: `zzz_ready`、`zzz_unread_mentee_to_read`、`subimg_upload_curriculum (copy)`
7. **名前のずれ**: `progress`→Records、`agency1`→Pertners（つづり違い）、`share_comment1`→MentorNote、`notyfy`（Option Set）。項目 `already_read_stylist` の表示名が unread_mentors、`assistant_read` が unread_mentee で意味が逆

## TODO

### プッシュ通知（Progressier）

手順書: 「カミキュラム プッシュ通知の導入手順」（古川さん作成）

- [ ] 通知の範囲を決める
  - A案: 最初は feedback_message の1種類だけ（データトリガーの Only when に type を追加）。この type は両方向（メンター⇄学習者）を含む
  - B案: 最初から全種類（本文が空の通知に固定文が必要）
  - 提案: A案で1本届くのを確認してから、type の条件を外して全種類に広げる
- [ ] Progressier の登録と設定（ドメイン app.kamiculum.com、Start URL `/curriculum_list`）
- [ ] プラグインの API Key 設定を確認（プラグインは導入済み）
- [ ] Header に新しいHTML要素を追加（ID `progressier-email-container`、中身は Current User's email）。既存の「HTML A」は見た目用なので書き換えない
- [ ] データトリガー `send_push_on_notification` を作成
- [ ] ライブにデプロイして実機で確認

### セキュリティ

- [ ] 各データタイプのプライバシールールを見直す
- [ ] `line_webhook` / `stripe_payment_succeeded` の送信元検証を確認
