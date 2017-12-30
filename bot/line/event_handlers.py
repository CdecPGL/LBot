import sys

import linebot

import bot.line.line_settings as line_settings
import bot.line.line_utilities as line_util
import bot.message_commands as mess_cmd
import bot.utilities as util
from bot.exceptions import GroupNotFoundError, UserNotFoundError

COMMAND_TRIGGER_LIST = ["#", "＃"]

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
        reply = 'よろしくお願いしますლ(´ڡ`ლ)\n"{0}[コマンド内容]"でコマンド実行\n"{0}使い方"で使い方を表示するよ'.format(
            "又は".join(COMMAND_TRIGGER_LIST))
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
    try:
        '''テキストメッセージを処理する'''
        message_text = util.unify_newline_code(event.message.text)
        # コマンドとパラメータの取得
        command_param = None
        if event.source.type == "user":
            command_param = message_text
        elif event.source.type == "group":
            # 送信元がユーザーでないグループの場合はコマンドトリガーを確認する
            hit_command_trigger_list = [
                command_trigger for command_trigger in COMMAND_TRIGGER_LIST if message_text.startswith(command_trigger)]
            if hit_command_trigger_list:
                command_param = message_text[len(hit_command_trigger_list[0]):]
        else:
            sys.stderr.write('送信元"{}"には対応していません。\n'.format(event.source.type))
            return

        # コマンドとパラメータの抽出
        command = None
        params = []
        if command_param:
            items = command_param.split("\n")
            print(items)
            command = items[0]
            if len(items) > 1:
                params = items[1:]

        # コマンドを実行し返信を送信。コマンドがない(自分宛てのメッセージではない)場合は返信しない
        if command:
            # メッセージ送信グループをデータベースから検索し、なかったら作成
            try:
                source_group = line_util.get_group_by_line_group_id_from_database(
                    event.source.group_id) if event.source.type == "group" else None
            except GroupNotFoundError:
                source_group = line_util.register_group_by_line_group_id(
                    event.source.group_id)
            # メッセージ送信者をデータベースから検索し、なかったら作成
            try:
                source_user = line_util.get_user_by_line_user_id_from_database(
                    event.source.user_id)
            except UserNotFoundError:
                if source_group:
                    source_user = line_util.register_user_by_line_user_in_group_id(
                        event.source.user_id, event.source.group_id)
                else:
                    source_user = line_util.register_user_by_line_user_id(
                        event.source.user_id)
            # コマンド実行
            command_source = mess_cmd.CommandSource(source_user, source_group)
            reply = mess_cmd.execute_command(command, command_source, params)
            # グループの時は宛先を表示
            if source_group:
                reply = "@{}\n{}".format(source_user.name, reply)
            line_settings.api.reply_message(
                event.reply_token,
                linebot.models.TextSendMessage(text=reply))
    except Exception:
        try:
            line_settings.api.reply_message(
                event.reply_token,
                linebot.models.TextSendMessage(text="なんかこっち側で問題が起こった。"))
        except Exception:
            pass
        raise
