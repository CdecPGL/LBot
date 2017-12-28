import random
from bot.models import Vocabulary

word_list = open("bot/word_list.txt").read().split("\n")


def generate_help():
    return '''<使い方>
    がんばれ。'''


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
        return text + "は知ってるけど、" + generate_random_word() + "じゃない？"
    except Vocabulary.DoesNotExist:
        # 新しい言葉は登録
        Vocabulary(word=text).save()
        return text + "はよく分からないけど、" + generate_random_word() + "だよね。"
