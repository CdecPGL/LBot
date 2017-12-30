'''返信生成関数群'''

from bot.models import Vocabulary

KNOW_BUT_LIST = ["は知ってるけど、", "は当たり前だね。でも",
                 "は最近はやってるよ。だけど", "は常識だよ。ところで", "はすごいよね。By the way, "]
UNKNOW_BUT_LIST = ["はよく分からないけど、", "はどうでもいいから、",
                   "は忘れた。話は変わって", "は消えたよ。ということで", "っておいしいの？", "? OK. Then "]
RANDOM_REPLY_SUFIX_LIST = ["じゃない？", "だよね。", "なんだって！",
                           "、はあ。", "らしいよ。知らんけど", "はクソ。", ", is it right?", "、喧嘩売ってんの？"]
MAX_VOCABLARY_COUNT = 100


def generate_random_word()->str:
    '''ランダムな単語を生成する'''
    if Vocabulary.objects.count():
        return Vocabulary.objects.order_by('?')[0].word
    else:
        return "何にも分からない……"


def generate_random_reply(text: str)->str:
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
