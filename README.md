# LuftelliBot

Luftelliのタスク管理などを行うボット。主にLINEのメッセージでコマンドを実行する。

## タイムゾーンについて

プログラム内や保存時にはUTC(協定世界時)で扱い、タスクの日時設定や表示にはデフォルトタイムゾーンを用いる。

デフォルトタイムゾーンは現在JST(日本時間)を用いている。
デフォルトタイムゾーンはbot/utilities.py内で定義されている。

システムのタイムゾーンはUTCに設定しておくこと。

## サーバー

現在はHerokuの無料プランを使用している。

## Herokuのスリープ対策

Herokuの無料プランでは接続が30分間ないとスリープされてしまい、タスクの定期確認が行われなくなってしまう。

これを防ぐために、GoogleAppsScriptを用いて定期的にHeroku上のLuftelliBotアプリにリクエストを送信している。

[AvoidSleepInHeroku](https://script.google.com/d/1SxPRRSzJwLZYuoplcZIB8_zDC0ETzcupac84mIDmmRa7ugpsLOqzljiG/edit?usp=sharing)
