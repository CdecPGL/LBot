import random
from bot.models import Vocabulary

KNOW_BUT_LIST=["は知ってるけど、", "は当たり前だね。でも","は最近はやってるよ。だけど","は常識だよ。ところで","はすごいよね。By the way, "]
UNKNOW_BUT_LIST=["はよく分からないけど、", "はどうでもいいから、","は忘れた。話は変わって","は消えたよ。ということで","っておいしいの？　Then, "]
RANDOM_REPLY_SUFIX_LIST=["じゃない？", "だよね。","なんだって！","、はあ。","らしいよ。知らんけど","はクソ。",", is it right?","喧嘩売ってんの？"]

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
        Vocabulary(word=text).save()
        return text + random.choice(UNKNOW_BUT_LIST) + reply + random.choice(RANDOM_REPLY_SUFIX_LIST)
