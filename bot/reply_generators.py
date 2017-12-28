import random
from bot.models import Vocabulary

word_list = open("bot/word_list.txt").read().split("\n")


def generate_help():
    return '''<使い方>
    がんばれ。'''


def generate_random_word():
    if Vocabulary.objects.count():
        return Vocabulary.objects.order_by('?').values_list("word")[0]
    else:
        return "何にも分からない……"


def generate_random_reply(text):
    return text + "はよく分からないけど、" + generate_random_word() + "。"
