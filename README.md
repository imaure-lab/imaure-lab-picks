# 楽天ランキング → Instagram自動投稿ツール

楽天市場のリアルタイムランキングを取得し、前回取得時との差分から「新規ランクイン」「順位上昇」商品を検出、
キャプションを生成してInstagramに投稿するツールです。

> 楽天ウェブサービスに「検索サジェストAPI」という一般公開APIは存在しないため、
> トレンド検出は「リアルタイムランキングAPIのスナップショット差分」で代替しています。

## セットアップ

### 1. Python環境

```bash
cd rakuten_ig_bot
pip install -r requirements.txt
cp .env.example .env
```

### 2. 楽天アプリID・アクセスキーの取得

1. https://webservice.rakuten.co.jp/app/list にアクセスし、楽天会員でログイン
2. 「アプリID発行」からアプリを新規登録
3. 発行された **アプリケーションID**(UUID形式)を `.env` の `RAKUTEN_APP_ID` に設定
4. 同じ画面の **アクセスキー**(`pk_`から始まる文字列。目のアイコンで表示)を `.env` の `RAKUTEN_ACCESS_KEY` に設定
5. アプリの「編集」画面で、**実行環境のグローバルIPアドレスを許可リストに追加**する
   (現在のIPは `curl https://api.ipify.org` で確認可能。自宅回線が動的IPの場合、IPが変わると
   `CLIENT_IP_NOT_ALLOWED` エラーになるため、その都度再登録が必要)

### 3. Instagram APIの準備(Instagramログイン方式・Facebookページ連携不要)

1. Instagramで投稿用アカウントを作成し、「プロアカウントに切り替え」→ **ビジネス** を選択
2. https://developers.facebook.com/ でアプリを作成(ユースケース: 「Instagramでメッセージとコンテンツを管理」)
3. アプリの「アプリの役割」→「役割」→「Instagramテスターを追加」で投稿用アカウントを招待し、
   Instagram側(アカウントセンター →「あなたの情報とアクセス許可」→「アプリのリンク」)で承諾する
4. 「ユースケース」→ 追加した使用例 →「アクセス許可と機能」で以下を追加
   - `instagram_business_basic`
   - `instagram_business_content_publish`
5. 「Instagramログインによる API設定」タブ →「2. アクセストークンを生成する」で対象アカウントの
   「トークンを生成」をクリックし、Instagram側で許可
6. 表示された **Instagramアカウント ID** を `.env` の `IG_USER_ID` に、
   **アクセストークン**(一度しか表示されないので必ずコピー)を `IG_ACCESS_TOKEN` に設定

これらのアカウント作成・トークン発行はブラウザ上でユーザー自身の認証操作が必要なため、
Claude Codeでは代行できません。

> 旧来の「Facebookページ経由」の連携方法(Graph API Explorer での手動権限追加)は、
> このアカウントでは権限選択UIが機能しなかったため、上記のInstagramログイン方式に切り替えています。

### 4. 取得ジャンルの設定

`.env` の `RAKUTEN_GENRE_IDS` にカンマ区切りでジャンルIDを指定します(複数指定可)。
ジャンルIDは[楽天ジャンル検索API](https://webservice.rakuten.co.jp/documentation/ichiba-genre-search)で調べられます。

デフォルトは防災関連グッズ・パソコン周辺機器・家電・スマートフォン/タブレットの4ジャンルです。

### 5. Claude APIキー(投稿文生成用・任意/現在未設定)

`ANTHROPIC_API_KEY` を設定するとClaudeが自然な日本語キャプションを生成します。
未設定の場合はテンプレートベースの簡易文を生成します(従量課金のため現在は保留中)。

## 使い方

### パターンA: その場で確認しながら投稿

```bash
python src/main.py
```

ランキング取得 → トレンド分析 → キャプション生成 → プレビュー表示 →
**確認プロンプトでYesと答えた場合のみ** Instagramに投稿します。

### パターンB: 都合の良いタイミングにずらして投稿(スケジュール実行向け)

投稿に最適な時間帯(19〜22時が目安)に自分で操作できない場合、生成と投稿を分離できます。

```bash
# ① 決まった時間に自動実行(下書き保存のみ、投稿はしない)
python src/generate_draft.py

# ② 都合の良いタイミングで手動実行(下書きを確認して投稿)
python src/approve_and_post.py
```

`generate_draft.py` はWindowsのタスクスケジューラで自動実行できます。

1. タスクスケジューラを開き「タスクの作成」
2. トリガー: 毎日 19:00 など
3. 操作: プログラム `python`、引数 `src\generate_draft.py`、開始場所 `D:\ClaudeCode\rakuten_ig_bot`

投稿(publish)は必ず `approve_and_post.py` 側の手動確認を挟みます(自動無人投稿はしません)。
