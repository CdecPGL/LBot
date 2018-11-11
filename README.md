# LBot

タスク管理などを行うボットです。LINEやDiscordのメッセージでコマンドを実行します。

## 環境変数

LBotでは一部の設定に環境変数を参照します。
Herokuの場合は以下のコマンドで設定できます。

```bash
heroku config:set ENV_VAR_NAME="value"
```

- LBOT_LINE_ACCESS_TOKEN: LINEのアクセストークン。必須。
- LBOT_LINE_CHANNEL_SECRET: LINEのチャンネルシークレット。必須。
- LBOT_DISCORD_TOKEN: Discordのトークン。オプション。
- LBOT_ENABLE_DEBUG_MODE: デバッグモードを有効にする場合は1を設定する。0に設定されているか定義されていない場合はデバッグモードは無効となる。オプション。

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

## プログラム構成

### LBot Core

Webフレームワークやメッセージサービスに依存しないLBotの中核部分。

#### イベント処理モジュール

フォローや参加などのイベントを処理するモジュール。

#### メッセージ解析モジュール

受け取ったメッセージを解析し、各種コマンドを発行するモジュール。

#### コマンド処理モジュール

受け取ったコマンドから各種操作を実行するモジュール。

#### 会話生成モジュール

会話を生成するモジュール。

#### Mediator

各種サービス間の違いを吸収する仲介クラス。

- SNS Mediator
- Task Management Service Mediator
- Database Mediator

### LBot Mediators

各種サービスをLbotが利用できるようにするための実装。

#### SNS Mediators

- LINE Mediator
- Didcord Mediator

#### Task Management Service Mediators

- Asana Mediator

#### Database Mediators

- Django Database Mediator

## Procfileについて

Djangoのauto reload昨日によるAppConfig.readyの二回呼び出し防止で、manager.pyの```--no_reload```オプションを使用するために、Procfileにおいてgunicornを使用した以下の内容ではなく、

```txt
web: gunicorn luftelli_bot.wsgi --log-file -
```

以下のように直接実行しています。

```txt
web: python manage.py runserver 0.0.0.0:$PORT --noreload
```

## LICENCE

このリポジトリのソースコードは[MITライセンス](LICENSE)のもと公開しています。
