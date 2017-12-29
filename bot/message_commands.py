import random
import sys
import inspect

from bot.models import Vocabulary

KNOW_BUT_LIST = ["は知ってるけど、", "は当たり前だね。でも",
                 "は最近はやってるよ。だけど", "は常識だよ。ところで", "はすごいよね。By the way, "]
UNKNOW_BUT_LIST = ["はよく分からないけど、", "はどうでもいいから、",
                   "は忘れた。話は変わって", "は消えたよ。ということで", "っておいしいの？", "? OK. Then "]
RANDOM_REPLY_SUFIX_LIST = ["じゃない？", "だよね。", "なんだって！",
                           "、はあ。", "らしいよ。知らんけど", "はクソ。", ", is it right?", "喧嘩売ってんの？"]
MAX_VOCABLARY_COUNT = 100


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


def help_command():
    '''ヘルプ'''
    return '<コマンド一覧>\n' + "\n".join(["■{}\n{}".format(name, inspect.getdoc(command_func)) for name, command_func in COMMAND_MAP.items()])


def test_command(*params):
    '''テストコマンド'''
    return "<コマンド引数>\n" + "\n".join(["{}: {}".format(idx + 1, param) for idx, param in enumerate(params)])


COMMAND_MAP = {
    "使い方": help_command,
    "テスト": test_command,
}


def execute_command(command, params):
    '''コマンド実行'''
    if command in COMMAND_MAP:
        try:
            command_func = COMMAND_MAP[command]
            return command_func(*params)
        except TypeError:
            sys.stderr.write("コマンドの実行でエラーが発生。({})".format(sys.exc_info()[1]))
            return "コマンド引数の数が不正です。使い方：\n" + inspect.getdoc(command_func)
    elif command is not None:
        return generate_random_reply(command)
    else:
        return None
