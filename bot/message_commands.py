import inspect
import random
import sys
from datetime import datetime

import bot.utilities as util
from bot.exceptions import GroupNotFoundError, UserNotFoundError
from bot.models import Group, Task, User, Vocabulary

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


def get_user_by_line_user_id_from_database(line_user_id):
    '''LINEのユーザーIDでデータベースからユーザーを取得する。ない場合は作成する'''
    try:
        return User.objects.get(line_user__user_id__exact=line_user_id)
    except User.DoesNotExist:
        raise UserNotFoundError(
            "ユーザー(LineUserID: {})が見つかりませんでした。".format(line_user_id))


def get_user_by_name_from_database(name):
    '''ユーザ名でデータベースからユーザーを取得する'''
    try:
        return User.objects.get(name__exact=name)
    except User.DoesNotExist:
        raise UserNotFoundError(
            "ユーザー(名前: {})が見つかりませんでした。".format(name))


def get_gropu_by_name_from_database(name):
    '''グループ名でデータベースからユーザーを取得する'''
    try:
        return Group.objects.get(name__exact=name)
    except Group.DoesNotExist:
        raise UserNotFoundError(
            "グループ(名前: {})が見つかりませんでした。".format(name))


def help_command(event):
    '''ヘルプ'''
    return '<コマンド一覧>\n' + "\n".join(["■{}\n{}".format(name, inspect.getdoc(command_func)) for name, command_func in COMMAND_MAP.items()]), []


def test_command(event, *params):
    '''テストコマンド'''
    return "<コマンド引数>\n" + "\n".join(["{}: {}".format(idx + 1, param) for idx, param in enumerate(params)]), []


def add_task_command(event, task_name, dead_line, user_participants=None, group_participants=None):
    '''タスクを追加します。メッセージの送信者がタスク管理者に設定されます。
    1: タスク名
    2: 期限
    (3: 、か,区切りで参加者を指定。デフォルトは送信者)
    (4: 、か,区切りで参加グループを指定。デフォルトはなし)'''
    # すでに同名のタスクがないか確認
    if Task.objects.filter(name__exact=task_name).count():
        return None, ["タスク「{}」はすでに存在します……".format(task_name)]
    try:
        error_list = []
        task_create_user = get_user_by_line_user_id_from_database(
            event.source.user_id)
        task_deadline = datetime()
        new_task = Task(name=task_name, dead_line=task_deadline)
        new_task.managers.add(task_create_user)
        # 参加者設定
        if user_participants:
            user_name_list = util.split_command_paramater_strig(
                user_participants)
            for user_name in user_name_list:
                try:
                    new_task.user_participants.add(
                        get_user_by_name_from_database(user_name))
                except UserNotFoundError as exce:
                    error_list.append(
                        "ユーザー「{}」が見つからないため、参加者に追加できませんでした。".format(user_name))
        else:
            new_task.user_participants.add(task_create_user)
        # 参加グループ設定
        if group_participants:
            group_name_list = util.split_command_paramater_strig(
                group_participants)
            for group_name in group_name_list:
                try:
                    new_task.group_participants.add(
                        get_gropu_by_name_from_database(group_name))
                except GroupNotFoundError as exce:
                    error_list.append(
                        "グループ「{}」が見つからないため、参加グループに追加できませんでした。".format(group_name))
        # データベースに保存
        new_task.save()
        return "タスクを作成しました。", error_list

    except UserNotFoundError as exce:
        sys.stderr.write(exce.message + "\n")
        return None, ["知らない人がタスクを作成しようとました……"]


def check_task_command(event, task_name, deadline):
    '''タスク確認コマンド'''
    pass


def remove_task_command(event):
    '''タスク削除コマンド'''


# 第一引数にイベントオブジェクト、第二引数以降にコマンドパラメータを取り、(返信,エラーリスト)を戻り値とする関数。返信がNoneの場合はコマンド失敗とみなす
COMMAND_MAP = {
    "使い方": help_command,
    "タスク追加": add_task_command,
    "タスク確認": check_task_command,
    "タスク削除": remove_task_command,
    "タスク編集": test_command,
    "ユーザー確認": test_command,
    "ユーザー編集": test_command,
    "テスト": test_command,
}


def execute_command(command, event,  params):
    '''コマンド実行。返信メッセージを返す'''
    if command in COMMAND_MAP:
        try:
            command_func = COMMAND_MAP[command]
            reply, errors = command_func(event, *params)
            if reply is None:
                errors.append("コマンド「{}」の実行に失敗しちゃった。。。".format(command))
            else:
                errors.append(reply)
            return "\n".join(errors)
        except TypeError:
            sys.stderr.write("コマンドの実行でエラーが発生。({})".format(sys.exc_info()[1]))
            return "コマンド引数の数が不正です。\n■「{}」コマンドの使い方\n".format(command) + inspect.getdoc(command_func)
    elif command is not None:
        return generate_random_reply(command)
    else:
        return "コマンドが指定されていません"
