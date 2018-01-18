# LBot

タスク管理などを行うボットです。LINEのメッセージでコマンドを実行します。

## 環境変数

LBotでは一部の設定に環境変数を参照します。
Herokuの場合は以下のコマンドで設定できます。

```bash
heroku config:set ENV_VAR_NAME="value"
```

- LBOT_LINE_ACCESS_TOKEN: ラインのアクセストークン。必須。
- LBOT_LINE_CHANNEL_SECRET: ラインのチャンネルシークレット。必須。
- LBOT_ENABLE_DEBUG_MODE: デバッグモードを有効にする場合は1を設定する。0に設定されているか定義されていない場合はデバッグモードは無効となる。

## タイムゾーンについて

プログラム内や保存時にはUTC(協定世界時)で扱い、タスクの日時設定や表示にはデフォルトタイムゾーンを用います。

デフォルトタイムゾーンは、bot/utilities.py内でJST(日本時間)に設定されています。

システムのタイムゾーンはUTCに設定してください。

## Herokuなどのスリープ対策

Herokuなどの無料プランでは接続が30分間ないとスリープされてしまい、タスクの定期確認が行われなくなってしまいます。
これを防ぐために、GoogleAppsScriptなどを用いて定期的にサーバー上のLBotアプリにリクエストを送信してください。
GoogleAppsScriptを用いる場合は以下のコードでスリープを防ぐことができます。

```js
function HerokuNotifier() {
  var url = "アプリURL";
  UrlFetchApp.fetch(url, { muteHttpExceptions:true });
}
```

## LICENCE

このリポジトリのソースコードは[MITライセンス](LICENSE)のもと公開しています。
