import sys

import linebot

import bot.line.line_settings as line_settings
import bot.message_commands as mess_cmd

COMMAND_TRIGGER = "ー！"

event_handler = linebot.WebhookHandler(line_settings.CHANNEL_SECRET)


@event_handler.add(linebot.models.FollowEvent)
def follow_event_handler(event):
    '''フォローイベントを処理する'''
    if event.source.type == "user":
        reply = 'よろしくお願いします（＾ν＾）\n"使い方"で使い方を表示するよ'
        line_settings.api.reply_message(
            event.reply_token,
            linebot.models.TextSendMessage(text=reply))
    else:
        sys.stderr.write(
            "フォローイベントで不正な送信元タイプ({})が指定されました。".format(event.sorce.type))


@event_handler.add(linebot.models.JoinEvent)
def join_event_handler(event):
    '''参加イベントを処理する'''
    if event.source.type == "group":
        reply = 'よろしくお願いしますლ(´ڡ`ლ)\n"{}[コマンド内容]"でコマンド実行\n"{}使い方"で使い方を表示するよ'.format(
            COMMAND_TRIGGER)
        line_settings.api.reply_message(
            event.reply_token,
            linebot.models.TextSendMessage(text=reply))
    elif event.source.type == "room":
        reply = 'トークルームには対応してないんです……\nさようなら(*_*)'
        line_settings.api.reply_message(
            event.reply_token,
            linebot.models.TextSendMessage(text=reply))
        line_settings.api.leave_room(event.source.room_id, timeout=None)
    else:
        sys.stderr.write(
            "参加イベントで不正な送信元タイプ({})が指定されました。".format(event.sorce.type))


@event_handler.add(linebot.models.MessageEvent, message=linebot.models.TextMessage)
def text_message_handler(event):
    '''テキストメッセージを処理する'''
    message_text = event.message.text
    # コマンドの取得
    command_param = None
    if event.source.type == "user":
        command_param = message_text
    else:
        # 送信元がユーザーでないグループの場合はコマンドトリガーを確認する
        if message_text.startswith(COMMAND_TRIGGER):
            command_param = message_text[len(COMMAND_TRIGGER):]
    command = None
    params = []
    if command_param:
        items = command_param.split("\n")
        command = items[0]
        if len(items) > 1:
            params = items[1:]

    # コマンド実行
    if command and command in mess_cmd.COMMAND_MAP:
        reply = mess_cmd.COMMAND_MAP[command](*params)
    else:
        reply = mess_cmd.generate_random_reply(message_text)

    # 返信を送信
    line_settings.api.reply_message(
        event.reply_token,
        linebot.models.TextSendMessage(text=reply))
