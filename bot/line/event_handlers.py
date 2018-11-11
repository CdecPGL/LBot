'''LINEイベントのハンドラ'''

import sys
import traceback

import linebot
from django.db.utils import OperationalError

from lbot import utilities as util
from lbot.exceptions import GroupNotFoundError, UserNotFoundError
from lbot.module.message_analysis import analyse_message_and_execute_command

from . import settings as line_settings
from . import utilities as line_util

COMMAND_TRIGGER_LIST = ["#", "＃"]
SENTENCE_MAX_LENGTH = 64

event_handler = None


def register_event_handlers():
    '''イベントハンドラを登録する'''
    global event_handler
    event_handler = linebot.WebhookHandler(line_settings.channel_secret)

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
            print(f"<LINEでメッセージを受信>\n{message_text}")
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
                    command_param = message_text[len(
                        hit_command_trigger_list[0]):]
            else:
                sys.stderr.write(
                    '送信元"{}"には対応していません。\n'.format(event.source.type))
                raise Reject("グループラインか個人ラインで話そう、、、")

            # メンテナンス中なら中断
            if util.ENABLE_MAINTENANCE_MODE:
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
                            linebot.models.TextSendMessage(text="「{}」をユーザー登録しました。".format(source_user.name)))

                except linebot.exceptions.LineBotApiError:
                    sys.stderr.write("LINEからユーザーのプロファイルを取得できませんでした。送信元タイプ: {}, LINEグループID: {}, LINEユーザーID: {}\n".format(
                        event.source.type, event.source.group_id, event.source.user_id))
                    raise Reject(
                        "送信ユーザーの情報をLINEから取得できませんでした。\n公式アカウントの利用条件に合意していない場合は合意する必要があります。\nまた、LINEのバージョンは7.5.0以上である必要があります。")

            # メッセージ解析とコマンド実行、その返信を行う
            is_success, reply = analyse_message_and_execute_command(
                command_param, source_user, source_group)
            if not is_success:
                raise Reject(reply)
            if reply:
                line_settings.api.reply_message(
                    event.reply_token,
                    linebot.models.TextSendMessage(text=f"@{source_user.name}\n{reply}"))

        except Reject as reject:
            line_settings.api.reply_message(
                event.reply_token,
                linebot.models.TextSendMessage(text=f"@{source_user.name}\n{reject.message}"))
            return
        except OperationalError:
            sys.stderr.write(
                "データベース操作でエラーが発生しました。({})\n".format(sys.exc_info()[1]))
            line_settings.api.reply_message(
                event.reply_token,
                linebot.models.TextSendMessage(text="内部エラー(データベース操作でエラーが発生)"))
            raise
        except Exception as e:
            traceback.print_exc()
            try:
                line_settings.api.reply_message(
                    event.reply_token,
                    linebot.models.TextSendMessage(text=f"内部で未処理のエラーが発生。詳細はログを見てね☆\n{e}"))
            except Exception:
                pass
            raise e
