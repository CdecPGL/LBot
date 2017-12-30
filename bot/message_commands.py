'''メッセージによるコマンド関連'''

import datetime
import inspect
import random
import sys

from dateutil.parser import parse as datetime_parse

import bot.utilities as util
from bot.authorities import UserAuthority
from bot.exceptions import GroupNotFoundError, UserNotFoundError, TaskNotFoundError
from bot.models import Group, Task, User, Vocabulary
import bot.database_utilities as db_util

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


def check_task_group_authority(command_source: CommandSource, task: Task):
    '''グループにタスクの編集閲覧権限があるかどうか。
    タスクの関連グループに含まれていたら権限があるとみなす。
    グループが発信元でない場合は常に権限があるとみなす。'''
    return not command_source.group_data or task.groups.filter(id__exact=command_source.group_data.id).exists()


def check_task_edit_autority(command_source: CommandSource, task: Task):
    '''ユーザーにタスクの編集権限があるかどうか。
    Masterユーザーかタスク管理者ならあるとみなす。'''
    return UserAuthority[command_source.user_data.authority] == UserAuthority.Master or task.managers.filter(id__exact=command_source.user_data.id).exists()


def check_task_watch_autority(command_source: CommandSource, task: Task):
    '''ユーザーにタスクの閲覧権限があるかどうか。
    編集権限を持っているか、参加者であるか、関連グループのメンバーなら権限があるとみなす。'''
    if check_task_edit_autority(command_source, task):
        return True
    else:
        return False


def check_task_group_edit_authority(command_source: CommandSource, task: Task)->(bool, str):
    '''タスクの編集権限があるかどうかを確認する。
    グループが発信元の場合は、タスクの関連グループに含まれている必要がある。
    加えて、発信元ユーザーがMasterユーザーであるか、タスクの管理者であるならTrueを返す。'''
    has_group_authority = check_task_group_authority(command_source, task)
    has_edit_authority = check_task_edit_autority(command_source, task)
    if has_group_authority:
        if has_edit_authority:
            return True, None
        else:
            return False, "編集権限がありません。コマンドの実行者がMasterユーザーかタスク管理者である必要があります。"
    else:
        if has_edit_authority:
            return False, "このグループはタスクの関連グループに含まれていません。個人ラインならコマンドを実行できます。"
        else:
            return False, "このグループはタスクの関連グループに含まれていません。"


def check_task_group_watch_authority(command_source: CommandSource, task: Task)->(bool, str):
    '''タスクの閲覧権限があるかどうかを確認する。
    グループが発信元の場合は、タスクの関連グループに含まれている必要がある。
    タスクの編集権限を持っているか、タスクの参加者か、タスクの関連グループのメンバーである場合にはTrueを返す。'''
    has_group_authority = check_task_group_authority(command_source, task)
    has_watch_authority = check_task_watch_autority(command_source, task)
    if has_group_authority:
        if has_watch_authority:
            return True, None
        else:
            return False, "閲覧権限がありません。コマンドの実行者がMasterユーザーかタスクの管理者、参加者、関連グループのメンバーのいずれかである必要があります。"
    else:
        if has_watch_authority:
            return False, "このグループはタスクの関連グループに含まれていません。個人ラインならコマンドを実行できます。"
        else:
            return False, "このグループはタスクの関連グループに含まれていません。"


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
        reply = 'グループの場合は「#」を先頭に付けて、個人ラインの場合は何も付けずに、コマンドを指定して実行することができます。\n'
        reply += 'コマンドでない文字列を指定した場合はてきとうな返事を返します。'
        reply += 'また、「使い方」コマンドにコマンド名を指定することでそのコマンドの詳細説明を表示します。\n'
        reply += '<コマンド一覧>\n' + "\n".join(command_list)
        return reply, []


@add_command_handler("ユーザー確認", UserAuthority.Watcher)
@add_command_handler("ユーザー編集", UserAuthority.Watcher)
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
    (3: 、か,区切りで参加者を指定。デフォルトは送信者。「全員」で関連グループ全員を指定。ただし「全員」と個別指定は併用不可)
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
                        db_util.get_group_by_name_from_database(group_name))
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
                valid_participant_name_list.append("関連グループの全員")
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
                        db_util.get_user_by_name_from_database(user_name))
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
    except Exception:
        new_task.delete()
        raise


@add_command_handler("タスク列挙", UserAuthority.Watcher)
def list_task_command(command_source: CommandSource, target: str = None, name: str = None)->(str, [str]):
    '''タスクの一覧を表示します(未実装)。
    ■コマンド引数
    1: タスク名又はタスク短縮名。タスク名を優先して検索されます'''
    return None, ["未実装"]


@add_command_handler("タスク詳細", UserAuthority.Watcher)
def check_task_command(command_source: CommandSource, target_task_name: str)->(str, [str]):
    '''タスクの詳細を表示します。
    グループラインの場合はそのグループがタスクの関連グループに含まれていることを条件とし、Masterユーザー、タスクの参加者、タスクの関連グループのメンバーのみ表示可能です。
    ■コマンド引数
    1: タスク名又はタスク短縮名'''
    try:
        task = db_util.get_task_by_name_or_shot_name_from_database(
            target_task_name)
        # Masterユーザー、管理者、参加者、関連グループのメンバーのみ閲覧可能
        has_authority, authority_error = check_task_group_watch_authority(
            command_source, task)
        if has_authority:
            reply = "<タスク「{}」詳細>\n".format(target_task_name)
            reply += "■短縮名\n{}\n".format(
                task.short_name if task.short_name else "未設定")
            reply += "■期限\n{}\n".format(
                task.deadline.strftime('%Y/%m/%d %H:%M:%S'))
            # 参加者
            if task.is_participate_all_in_groups:
                participants_str = "関連グループの全員"
            elif task.participants.exists():
                participants_str = ",".join(
                    [participant.name for participant in task.participants.all()])
            else:
                participants_str = "なし"
            reply += "■参加者\n{}\n".format(participants_str)
            # 関連グループ
            if task.groups.exists():
                groups_str = ",".join(
                    [group.name for group in task.groups.all()])
            else:
                groups_str = "なし"
            reply += "■関連グループ\n{}\n".format(groups_str)
            return reply, []
        else:
            return None, [authority_error]
    except TaskNotFoundError:
        return None, ["タスク「{}」が見つからない！".format(target_task_name)]


@add_command_handler("タスク削除", UserAuthority.Editor)
def remove_task_command(command_source: CommandSource, target_task_name)->(str, [str]):
    '''タスクを削除します。
    グループラインの場合はそのグループがタスクの関連グループに含まれていることを条件とし、Masterユーザー、タスクの管理者のみ削除可能です。
    ■コマンド引数
    1: タスク名又はタスク短縮名'''
    try:
        task = db_util.get_task_by_name_or_shot_name_from_database(
            target_task_name)
        # Masterユーザーか、そのタスクの管理者のみ削除可能
        has_authority, authority_error = check_task_group_edit_authority(
            command_source, task)
        if has_authority:
            task.delete()
            return "タスク「{}」を削除しました。".format(target_task_name), []
        else:
            return None, [authority_error]
    except TaskNotFoundError:
        return None, ["タスク「{}」が見つからない！".format(target_task_name)]


@add_command_handler("タスク編集", UserAuthority.Editor)
def edit_task_command(command_source: CommandSource)->(str, [str]):
    '''タスクを編集をします(未実装)。
    Editor権限以上のユーザーでないとタスク管理者にはなれません。
    タスク管理者がいなくなるような変更は行えません。
    タスクの短縮名は全てタスク名、他のタスク短縮名と重複することはできません。
    Masterユーザーかタスクの管理者のみ変更可能です。'''
    return None, ["未実装"]


@add_command_handler("ユーザー権限変更", UserAuthority.Master)
def change_user_authority(command_source: CommandSource, target_user_name: str, target_authority: str):
    '''ユーザーの権限を変更します。
    Master権限を持つユーザーがいなくなるような変更は行えません。
    管理しているタスクがあるユーザーをWatcher権限にすることはできません。
    ■コマンド引数
    1: 対象のユーザー名
    2: 権限。「Master」、「Editor」、「Watcher」のいずれか'''
    try:
        user = db_util.get_user_by_name_from_database(target_user_name)
        try:
            current_authority = UserAuthority[user.authority]
            target_authority = UserAuthority[target_authority]
        except KeyError:
            return None, ["指定された権限「{}」は存在しないよ。".format(target_authority)]
        # 変更の必要があるか確認
        if current_authority == target_authority:
            return "変更は必要ないよ。", []
        # Masterユーザーの数を確認
        if current_authority == UserAuthority.Master:
            if User.objects.filter(authority__exact=UserAuthority.Master.name).count() == 1:
                return None, ["Masterユーザーがいなくなっちゃうよ。"]
        # 管理タスクがないか確認
        if target_authority == UserAuthority.Watcher:
            if user.managing_tasks.exists():
                return [None, "ユーザー「{}」には管理しているタスクがあるので「{}」権限には変更できないよ。".format(target_user_name, UserAuthority.Watcher.name)]
        # 権限変更
        user.authority = target_authority.name
        user.save()
        return "ユーザー「{}」の権限を「{}」から「{}」に変更したよ。".format(target_user_name, current_authority.name, target_authority.name), []
    except UserNotFoundError:
        return None, ["指定されたユーザー「{}」はいないよ。".format(target_user_name)]


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
