'''メッセージによるコマンド関連'''

import datetime
import inspect
import random
import sys

from dateutil.parser import parse as datetime_parse

import bot.utilities as util
from bot.authorities import UserAuthority
from bot.exceptions import GroupNotFoundError, UserNotFoundError
from bot.models import Group, Task, User, Vocabulary

KNOW_BUT_LIST = ["は知ってるけど、", "は当たり前だね。でも",
                 "は最近はやってるよ。だけど", "は常識だよ。ところで", "はすごいよね。By the way, "]
UNKNOW_BUT_LIST = ["はよく分からないけど、", "はどうでもいいから、",
                   "は忘れた。話は変わって", "は消えたよ。ということで", "っておいしいの？", "? OK. Then "]
RANDOM_REPLY_SUFIX_LIST = ["じゃない？", "だよね。", "なんだって！",
                           "、はあ。", "らしいよ。知らんけど", "はクソ。", ", is it right?", "、喧嘩売ってんの？"]
MAX_VOCABLARY_COUNT = 100

EVERYONE_WORD = "全員"


class CommandSource(object):
    '''コマンド送信元のデータ'''

    def __init__(self, user_data: User, group_data: Group):
        self.user_data = user_data
        self.group_data = group_data


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


def get_user_by_name_from_database(name: str)->User:
    '''ユーザ名でデータベースからユーザーを取得する'''
    try:
        return User.objects.get(name__exact=name)
    except User.DoesNotExist:
        raise UserNotFoundError(
            "ユーザー(名前: {})が見つかりませんでした。".format(name))


def get_group_by_name_from_database(name: str)->Group:
    '''グループ名でデータベースからユーザーを取得する'''
    try:
        return Group.objects.get(name__exact=name)
    except Group.DoesNotExist:
        raise GroupNotFoundError(
            "グループ(名前: {})が見つかりませんでした。".format(name))


__command_map = {}


def add_command_handler(command_name, authority):
    '''コマンドハンドラを追加するデコレータ。
    第一引数にコマンド送信元、第二引数以降にコマンドパラメータを取り、(返信,エラーリスト)を戻り値とする関数を登録する。
    返信がNoneの場合はコマンド失敗とみなす。'''
    def decorator(func):
        decorator.__doc__ = func.__doc__
        __command_map[command_name] = (func, authority)
    return decorator


@add_command_handler("使い方", UserAuthority.Watcher)
def help_command(command_source: CommandSource, target_command_name: str = None)->(str, [str]):
    '''使い方を表示します。コマンドの指定がない場合はコマンドの一覧を表示します。
    ■コマンド引数
    (1: 使い方を見たいコマンド名)'''
    # コマンド一覧の作成。各コマンドの説明文は一行目のみを取り出したもの
    command_list = []
    for command_name, (command_func, command_authority) in __command_map.items():
        command_doc = inspect.getdoc(command_func)
        simple_doc = command_doc.split("\n")[0] if command_doc else "未設定"
        command_list.append("■{}(権限：{})\n{}".format(
            command_name, command_authority.name, simple_doc))
    # ターゲットが指定されていたらそのコマンドの詳細を表示
    if target_command_name:
        if target_command_name in __command_map:
            command_func, command_authority = __command_map[target_command_name]
            return "<「{}」コマンドの使い方>\n■必要権限\n{}\n■説明\n{}".format(target_command_name, command_authority.name, inspect.getdoc(command_func)), []
        else:
            return "「{}」コマンドは存在しません。\n<コマンド一覧>\n{}".format(target_command_name, "\n".join(command_list)), []
    # 指定されていなかったらコマンドリストを表示
    else:
        return '「使い方」コマンドにコマンド名を指定することで、そのコマンドの詳細説明を表示します。\n<コマンド一覧>\n' + "\n".join(command_list), []


@add_command_handler("タスク編集", UserAuthority.Watcher)
@add_command_handler("ユーザー確認", UserAuthority.Watcher)
@add_command_handler("ユーザー編集", UserAuthority.Watcher)
@add_command_handler("ユーザー権限変更", UserAuthority.Master)
@add_command_handler("グループ編集", UserAuthority.Watcher)
@add_command_handler("議事録開始", UserAuthority.Editor)
@add_command_handler("議事録終了", UserAuthority.Editor)
@add_command_handler("テスト", UserAuthority.Master)
def test_command(command_source: CommandSource, *params)->(str, [str]):
    '''テストコマンド'''
    reply = '<送信者>\n'
    reply += 'LineUserID: {}\n'.format(
        command_source.user_data.line_user.user_id)
    reply += 'Name: {}\n'.format(command_source.user_data.name)
    reply += '<送信元グループ>\n'
    if command_source.group_data:
        line_group_id = command_source.group_data.line_group.group_id
        group_name = command_source.group_data.name if command_source.group_data.name else '未設定'
    else:
        line_group_id = "なし"
        group_name = "なし"
    reply += 'LineGroupID: {}\n'.format(line_group_id)
    reply += 'Name: {}\n'.format(group_name)
    reply += '<コマンド引数>\n'
    reply += "\n".join(["{}: {}".format(idx + 1, param)
                        for idx, param in enumerate(params)])
    return reply, []


@add_command_handler("タスク追加", UserAuthority.Editor)
def add_task_command(command_source: CommandSource, task_name: str, dead_line: str, participants: str=None, groups: str=None)->(str, [str]):
    '''タスクを追加します。
    メッセージの送信者がタスク管理者に設定されます。タスク管理者はそのタスクのあらゆる操作を実行できます。
    参加者はそのタスクの情報を参照することができ、期限が近づくと通知されます。
    また、グループを設定すると、そのグループメンバーは参加者でなくてもそのタスクを参照できます。
    ■コマンド引数
    1: タスク名
    2: 期限。"年/月/日 時:分"の形式で指定。年や時間は省略可能
    (3: 、か,区切りで参加者を指定。デフォルトは送信者。「全員」で参加グループ全員)
    (4: 、か,区切りで参加グループを指定。デフォルトは送信元グループ)'''
    # すでに同名のタスクがないか確認
    if Task.objects.filter(name__exact=task_name).count():
        return None, ["タスク「{}」はすでに存在します……".format(task_name)]

    error_list = []
    task_create_user = command_source.user_data
    # 期限を変換
    try:
        task_deadline = datetime_parse(dead_line)
        if task_deadline <= datetime.datetime.now():
            return None, ["期限が過去になってるよ……"]
    except ValueError:
        return None, ["期限には日時をしてくださいいいいい！"]
    new_task = Task.objects.create(
        name=task_name, deadline=task_deadline, is_participate_all_in_groups=False)
    new_task.managers.add(task_create_user)
    try:
        # 参加グループ設定
        valid_group_name_list = []
        # グループが指定されていたらそれを設定
        if groups:
            group_name_list = util.split_command_paramater_strig(
                groups)
            for group_name in group_name_list:
                try:
                    new_task.groups.add(
                        get_group_by_name_from_database(group_name))
                    valid_group_name_list.append(group_name)
                except GroupNotFoundError:
                    error_list.append(
                        "グループ「{}」が見つからないため、参加グループに追加できませんでした。".format(group_name))
        # グループが指定されていなくて送信元がグループならそれを設定
        if not valid_group_name_list and command_source.group_data:
            new_task.groups.add(command_source.group_data)
            valid_group_name_list.append("このグループ")

        # 参加者設定
        valid_participant_name_list = []
        # 全員参加なら全員参加フラグを設定
        if participants == EVERYONE_WORD:
            if valid_group_name_list:
                new_task.is_participate_all_in_groups = True
                valid_participant_name_list.append("指定グループの全員")
            else:
                new_task.delete()
                return None, ["参加者にグループメンバー全員が指定されたけど、グループが指定されてないよ。。。"]
        # 参加者が指定されていたらそれを設定
        elif participants:
            participant_name_list = util.split_command_paramater_strig(
                participants)
            for user_name in participant_name_list:
                try:
                    new_task.participants.add(
                        get_user_by_name_from_database(user_name))
                    valid_participant_name_list.append(user_name)
                except UserNotFoundError:
                    error_list.append(
                        "ユーザー「{}」が見つからないため、参加者に追加できませんでした。".format(user_name))
        # 参加者が指定されていなかったら送信者を設定
        if not valid_participant_name_list:
            new_task.participants.add(task_create_user)
            valid_participant_name_list.append(task_create_user.name)
        # データベースに保存
        new_task.save()
        reply = "「{}」タスクを作成し、期限を{}に設定しました。\n".format(
            task_name, task_deadline.strftime('%Y/%m/%d %H:%M:%S'))
        reply += "■関連グループ\n{}\n".format("、".join(valid_group_name_list)
                                        if valid_group_name_list else "なし")
        reply += "■参加者\n{}".format("、".join(valid_participant_name_list))
        return reply, error_list
    # 途中でエラーになったら作成したタスクは削除する
    except:
        new_task.delete()
        raise


@add_command_handler("タスク確認", UserAuthority.Watcher)
def check_task_command(command_source: CommandSource)->(str, [str]):
    '''タスク確認コマンド'''
    pass


@add_command_handler("タスク削除", UserAuthority.Watcher)
def remove_task_command(command_source: CommandSource)->(str, [str]):
    '''タスク削除コマンド'''
    pass


def execute_command(command: str, command_source: CommandSource, params: [str]):
    '''コマンド実行。返信メッセージを返す'''
    if command in __command_map:
        command_func, command_authority = __command_map[command]
        # 権限の確認
        user_authority = UserAuthority[command_source.user_data.authority]
        if user_authority.check(command_authority):
            try:
                inspect.signature(command_func).bind(command_source, *params)
            except TypeError:
                sys.stderr.write(
                    "コマンドの実行でエラーが発生。({})\n".format(sys.exc_info()[1]))
                return "コマンド引数の数が不正です。\n■「{}」コマンドの使い方\n{}".format(command, inspect.getdoc(command_func))
            reply, errors = command_func(command_source, *params)
        else:
            reply = None
            errors = ["お前にそんな権限はないよ。お前の権限：{}、コマンドの要求権限：{}。権限の変更はMasterユーザーに頼んでネ^_^".format(
                user_authority.name, command_authority.name)]
        # 結果を返す
        if reply is None:
            errors.append("コマンド「{}」の実行に失敗しちゃった。。。".format(command))
        else:
            errors.append(reply)
        return "\n".join(errors)
    elif command is not None:
        return generate_random_reply(command)
    else:
        return "コマンドが指定されていません"
