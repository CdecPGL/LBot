import random
import sys

import linebot

import bot.line.line_settings as line_settings
from bot.models import Vocabulary

KNOW_BUT_LIST = ["は知ってるけど、", "は当たり前だね。でも",
                 "は最近はやってるよ。だけど", "は常識だよ。ところで", "はすごいよね。By the way, "]
UNKNOW_BUT_LIST = ["はよく分からないけど、", "はどうでもいいから、",
                   "は忘れた。話は変わって", "は消えたよ。ということで", "っておいしいの？", "? OK. Then "]
RANDOM_REPLY_SUFIX_LIST = ["じゃない？", "だよね。", "なんだって！",
                           "、はあ。", "らしいよ。知らんけど", "はクソ。", ", is it right?", "喧嘩売ってんの？"]
MAX_VOCABLARY_COUNT = 100
COMMAND_TRIGGER = "ー！"

event_handler = linebot.WebhookHandler(line_settings.CHANNEL_SECRET)


def generate_help():
    return '''使い方(未実装)'''


def generate_random_word():
    '''ランダムな単語を生成する'''
    if Vocabulary.objects.count():
        return Vocabulary.objects.order_by('?')[0].word
    else:
        return "何にも分からない……"


def generate_random_reply(text):
    '''返信を生成する'''
    # 投げかけられた言葉を検索
    try:
        Vocabulary.objects.get(word__iexact=text)
        return text + random.choice(KNOW_BUT_LIST) + generate_random_word() + random.choice(RANDOM_REPLY_SUFIX_LIST)
    except Vocabulary.DoesNotExist:
        # 新しい言葉は登録
        reply = generate_random_word()
        # 語彙数が指定数を超えていたらランダムに一つ削除
        if Vocabulary.objects.count() > MAX_VOCABLARY_COUNT:
            Vocabulary.objects.order_by('?')[0].delete()
        # 新しい単語を登録
        Vocabulary(word=text).save()
        return text + random.choice(UNKNOW_BUT_LIST) + reply + random.choice(RANDOM_REPLY_SUFIX_LIST)


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
    # 送信元がユーザーでないグループの場合はコマンドトリガーを確認する
    message_text = event.messege.text
    if event.source.type != "user":
        message_text.startswith(COMMAND_TRIGGER)

    if event.message.text == "使い方":
        reply = generate_help()
    else:
        reply = generate_random_reply(event.message.text)
    line_settings.api.reply_message(
        event.reply_token,
        linebot.models.TextSendMessage(text=reply))
