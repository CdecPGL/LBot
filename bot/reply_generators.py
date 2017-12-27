import random

word_list = open("bot/word_list.txt").read().split("\n")

def generate_help():
    return '''<使い方>
    がんばれ。'''

def generate_random_word():
    return random.choice(word_list)

def generate_random_reply(text):
    return text + "はよく分からないけど、" + generate_random_word() + "。"
