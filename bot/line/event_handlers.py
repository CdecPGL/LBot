'''LINEイベントのハンドラ'''

import sys

import linebot
from django.db.utils import OperationalError

from lbot import utilities as util
from lbot.exceptions import GroupNotFoundError, UserNotFoundError
from lbot.module import message_command as mess_cmd

from . import line_settings
from . import line_utilities as line_util

COMMAND_TRIGGER_LIST = ["#", "＃"]
SENTENCE_MAX_LENGTH = 64

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
    '''テキストメッセージを処理する'''
    class Reject(Exception):
        '''リジェクト例外'''

        def __init__(self, message: str):
            super(Reject, self).__init__()
            self.message = message

    try:
        message_text = util.unify_newline_code(event.message.text)
        # コマンドとパラメータの取得
        command_param = None
        if event.source.type == "user":
            command_param = message_text
        elif event.source.type == "group":
            # 送信元がユーザーでないグループの場合はコマンドトリガーを確認する
            # メッセージがコマンド開始文字列と全く同じ場合はリジェクト
            if any([command_trigger for command_trigger in COMMAND_TRIGGER_LIST if message_text == command_trigger]):
                raise Reject("なんか言いたまへ(@_@)")
            hit_command_trigger_list = [
                command_trigger for command_trigger in COMMAND_TRIGGER_LIST if message_text.startswith(command_trigger)]
            if hit_command_trigger_list:
                command_param = message_text[len(hit_command_trigger_list[0]):]
        else:
            sys.stderr.write('送信元"{}"には対応していません。\n'.format(event.source.type))
            raise Reject("グループラインか個人ラインで話そう、、、")

        # コマンドとパラメータの抽出
        command = None
        params = []
        if command_param:
            # 左右の空白は取り除く
            items = [item.strip() for item in command_param.split("\n")]
            print(items)
            # 文字列の長さが規定値を超えていたらリジェクト
            if any([len(item) > SENTENCE_MAX_LENGTH for item in items]):
                raise Reject("長文は受け付けません(´ε｀ )")
            # コマンド文字列が空だったらリジェクト
            if not items or not items[0]:
                raise Reject("もうちょっと喋って？")
            command = items[0]
            if len(items) > 1:
                params = items[1:]

        # コマンドが指定されてメンテナンス中なら中断
        if command and util.ENABLE_MAINTENANCE_MODE:
            raise Reject("メンテナンス中です。。。")

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
            # グループへメンバーが登録されているか確認し必要なら登録
            if source_group:
                if line_util.add_member_to_group_if_need(source_user, source_group):
                    # メンバーの追加を通知
                    line_settings.api.push_message(
                        source_group.line_group.group_id,
                        linebot.models.TextSendMessage(text="このグループ「{}」にユーザー「{}」を追加しました。".format(source_group.name, source_user.name)))
        except UserNotFoundError:
            try:
                if source_group:
                    source_user = line_util.register_user_by_line_user_id_in_group(
                        event.source.user_id, event.source.group_id)
                    # メンバーの追加を通知
                    line_settings.api.push_message(
                        source_group.line_group.group_id,
                        linebot.models.TextSendMessage(text="このグループ「{}」にユーザー「{}」を追加しました。".format(source_group.name, source_user.name)))
                else:
                    source_user = line_util.register_user_by_line_user_id(
                        event.source.user_id)
                    # ユーザーの登録を通知
                    line_settings.api.push_message(
                        source_user.line_user.user_id,
                        linebot.models.TextSendMessage(text="あなた「{}」をユーザー登録しました。".format(source_user.name)))

            except linebot.exceptions.LineBotApiError:
                sys.stderr.write("LINEからユーザーのプロファイルを取得できませんでした。送信元タイプ: {}, LINEグループID: {}, LINEユーザーID: {}\n".format(
                    event.source.type, event.source.group_id, event.source.user_id))
                raise Reject(
                    "送信ユーザーの情報をLINEから取得できませんでした。\n公式アカウントの利用条件に合意していない場合は合意する必要があります。\nまた、LINEのバージョンは7.5.0以上である必要があります。")

        # コマンドを実行し返信を送信。コマンドがない(自分宛てのメッセージではない)場合は返信しない
        if command:
            # コマンド実行
            command_source = mess_cmd.CommandSource(source_user, source_group)
            reply = mess_cmd.execute_message_command(
                command, command_source, params)
            # グループの時は宛先を表示
            if source_group:
                reply = "@{}\n{}".format(source_user.name, reply)
            line_settings.api.reply_message(
                event.reply_token,
                linebot.models.TextSendMessage(text=reply))
    except Reject as reject:
        line_settings.api.reply_message(
            event.reply_token,
            linebot.models.TextSendMessage(text=reject.message))
        return
    except OperationalError:
        sys.stderr.write(
            "データベース操作でエラーが発生しました。({})\n".format(sys.exc_info()[1]))
        line_settings.api.reply_message(
            event.reply_token,
            linebot.models.TextSendMessage(text="内部エラー(データベース操作でエラーが発生)"))
        raise
    except Exception:
        try:
            line_settings.api.reply_message(
                event.reply_token,
                linebot.models.TextSendMessage(text="なんかこっち側で謎の問題が起こった。"))
        except Exception:
            pass
        raise
