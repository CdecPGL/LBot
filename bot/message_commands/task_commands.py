'''タスク関連のメッセージコマンド'''

from datetime import datetime, timezone

from dateutil.parser import parse as datetime_parse

import bot.database_utilities as db_util
import bot.utilities as util
from bot.authorities import UserAuthority
from bot.exceptions import (GroupNotFoundError, TaskNotFoundError,
                            UserNotFoundError)
from bot.models import Task, User
from bot.utilities import TIMEZONE_DEFAULT

from .message_command import CommandSource, add_command_handler

EVERYONE_WORD = "全員"


def check_task_edit_authority(user: User, task: Task):
    '''ユーザーにタスクの編集権限があるかどうか。
    Masterユーザーかタスク管理者ならあるとみなす。'''
    return UserAuthority[user.authority] == UserAuthority.Master or task.managers.filter(id__exact=user.id).exists()


def check_if_task_participant(user: User, task: Task):
    '''ユーザーがタスクの参加者かどうか調べる。
    タスクの参加者になっているか、そのタスクがグループ全体参加の場合にタスクの関連グループにそのユーザーが入っている場合にTrue。'''
    if task.is_participate_all_in_groups:
        return task.participants.filter(id__exact=user.id).exists() or task.groups.filter(members__id=user.id)
    else:
        return task.participants.filter(id__exact=user.id).exists()


def check_task_watch_authority(user: User, task: Task):
    '''ユーザーにタスクの閲覧権限があるかどうか。
    編集権限を持っているか、参加者であるか、関連グループのメンバーなら権限があるとみなす。'''
    if check_task_edit_authority(user, task):
        return True
    else:
        is_participant = check_if_task_participant(user, task)
        is_related_member = task.groups.filter(members__id=user.id).exists()
        return is_participant or is_related_member


def get_user_belonging_tasks(user: User):
    '''ユーザーが参加しているタスクを取得する'''
    # ユーザーの参加タスク
    belonging_tasks = user.belonging_tasks.all()
    # 参加しているグループで全員指定されているタスク
    belonging_tasks = belonging_tasks | Task.objects.filter(
        groups__members__id=user.id, is_participate_all_in_groups=True)
    return belonging_tasks


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
        # タイムゾーン情報がなかったらデフォルトのタイムゾーンで扱う
        if task_deadline.tzinfo is None:
            task_deadline = task_deadline.astimezone(TIMEZONE_DEFAULT)
        # UTCに変換
        task_deadline = task_deadline.astimezone(timezone.utc)
        if task_deadline <= datetime.now(timezone.utc):
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
            task_name, util.convert_datetime_in_default_timezone_to_string(task_deadline))
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
    '''タスクの一覧を表示します。
    Masterユーザー、タスクの参加者、タスクの関連グループのメンバーのみ閲覧可能です。
    ■コマンド引数
    (1: 「グループ」又は「ユーザー」。デフォルトは両方)
    (2: グループ又はユーザーの名前。デフォルトは送信者)'''
    def list_user_task(command_source: CommandSource, name: str):
        try:
            '''指定ユーザーのタスクをリストアップする'''
            user = db_util.get_user_by_name_from_database(name)
            task_name_deadline_list = [(task.name, task.deadline) for task in get_user_belonging_tasks(
                user).all() if check_task_watch_authority(user, task)]
            # 期限の近い順に並び替え
            task_name_deadline_list.sort(
                key=lambda name_deadline: name_deadline[1])
            if task_name_deadline_list:
                tasks_str = "\n".join(["{}: {}".format(name, util.convert_datetime_in_default_timezone_to_string(
                    deadline)) for name, deadline in task_name_deadline_list])
            else:
                tasks_str = "なし"
            return "■ユーザー「{}」のタスク一覧\n{}".format(name, tasks_str), []
        except UserNotFoundError:
            return None, ["ユーザー「{}」が見つからなかった。".format(name)]

    def list_group_task(command_source: CommandSource, name: str):
        '''指定グループのタスクをリストアップする'''
        try:
            group = db_util.get_group_by_name_from_database(name)
            task_name_deadline_list = [(task.name, task.deadline) for task in group.tasks.all(
            ) if check_task_watch_authority(command_source.user_data, task)]
            # 期限の近い順に並び替え
            task_name_deadline_list.sort(
                key=lambda name_deadline: name_deadline[1])
            if task_name_deadline_list:
                tasks_str = "\n".join(["{}: {}".format(name, util.convert_datetime_in_default_timezone_to_string(
                    deadline)) for name, deadline in task_name_deadline_list])
            else:
                tasks_str = "なし"
            return "■グループ「{}」のタスク一覧\n{}".format(name, tasks_str), []
        except GroupNotFoundError:
            return None, ["グループ「{}」が見つからなかった。".format(name)]

    if target == "グループ":
        if command_source.group_data:
            return list_group_task(command_source, name if name else command_source.group_data.name)
        else:
            return None, ["グループからのコマンドじゃないのでターゲットにグループを指定さしても意味ないよ。"]
    elif target == "ユーザー":
        return list_user_task(command_source, name if name else command_source.user_data.name)
    # ターゲットが指定されてなかったらグループとユーザーの両方を列挙
    elif target is None:
        reply, errors = list_user_task(
            command_source, command_source.user_data.name)
        # グループが送信元の場合のみグループは列挙
        if command_source.group_data:
            reply_group, error_group = list_group_task(
                command_source, command_source.group_data.name)
            reply += "\n" + reply_group
            errors.extend(error_group)
        return reply, errors
    else:
        return None, ["不明なターゲット「{}」が指定されました。ターゲットは「グループ」か「ユーザー」である必要があります。".format(target)]


@add_command_handler("タスク詳細", UserAuthority.Watcher)
def check_task_command(command_source: CommandSource, target_task_name: str)->(str, [str]):
    '''タスクの詳細を表示します。
    Masterユーザー、タスクの参加者、タスクの関連グループのメンバーのみ表示可能です。
    ■コマンド引数
    1: タスク名又はタスク短縮名'''
    try:
        task = db_util.get_task_by_name_or_shot_name_from_database(
            target_task_name)
        # Masterユーザー、管理者、参加者、関連グループのメンバーのみ閲覧可能
        if check_task_watch_authority(command_source.user_data, task):
            reply = "<タスク詳細>\n"
            reply += "■名前\n{}\n".format(target_task_name)
            reply += "■短縮名\n{}\n".format(
                task.short_name if task.short_name else "未設定")
            reply += "■期限\n{}\n".format(
                util.convert_datetime_in_default_timezone_to_string(task.deadline))
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
            reply += "■関連グループ\n{}".format(groups_str)
            return reply, []
        else:
            return None, ["タスクの閲覧権限がありません。タスクの閲覧はMasterユーザー、タスクの参加者、タスクの関連グループのメンバーのみ可能でーす。"]
    except TaskNotFoundError:
        return None, ["タスク「{}」が見つからない！".format(target_task_name)]


@add_command_handler("タスク削除", UserAuthority.Editor)
def remove_task_command(command_source: CommandSource, target_task_name)->(str, [str]):
    '''タスクを削除します。
    Masterユーザー、タスクの管理者のみ削除可能です。
    ■コマンド引数
    1: タスク名又はタスク短縮名'''
    try:
        task = db_util.get_task_by_name_or_shot_name_from_database(
            target_task_name)
        # Masterユーザーか、そのタスクの管理者のみ削除可能
        if check_task_edit_authority(command_source.user_data, task):
            task.delete()
            return "タスク「{}」を削除しました。".format(target_task_name), []
        else:
            return None, ["タスクの編集権限がありません。タスクの編集は Masterユーザー、タスクの管理者のみ可能ですー。"]
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
