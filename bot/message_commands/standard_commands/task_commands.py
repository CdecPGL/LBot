'''タスク関連のメッセージコマンド'''

from datetime import datetime, timezone

from dateutil.parser import parse as datetime_parse

from ... import database_utilities as db_util
from ... import utilities as util
from ...authorities import UserAuthority
from ...exceptions import (GroupNotFoundError, TaskNotFoundError,
                           UserNotFoundError)
from ...models import Task, TaskImportance, User
from ...utilities import TIMEZONE_DEFAULT
from ..check_task_commands import disable_task_check_command_if_need
from ..message_command import CommandSource
from .standard_command import StandardMessageCommandGroup

EVERYONE_WORD = "全員"


def check_task_edit_authority(user: User, task: Task):
    '''ユーザーにタスクの編集権限があるかどうか。
    Masterユーザーかタスク管理者ならあるとみなす。'''
    return UserAuthority[user.authority] == UserAuthority.Master or task.managers.filter(id__exact=user.id).exists()


def check_task_watch_authority(user: User, task: Task):
    '''ユーザーにタスクの閲覧権限があるかどうか。
    編集権限を持っているか、参加者であるか、関連グループのメンバーなら権限があるとみなす。'''
    if check_task_edit_authority(user, task):
        return True
    else:
        is_participant = task.participants.filter(id=user.id).exists()
        is_related_member = task.group.members.filter(id=user.id).exists()
        return is_participant or is_related_member


@StandardMessageCommandGroup.add_command("タスク追加", UserAuthority.Editor)
def add_task_command(command_source: CommandSource, task_name: str, dead_line: str, importance: str = None, participants: str=None, group_name: str=None)->(str, [str]):
    '''タスクを追加します。
    メッセージの送信者がタスク管理者に設定されます。タスク管理者はそのタスクのあらゆる操作を実行できます。
    参加者はそのタスクの情報を参照することができ、期限が近づくと通知されます。
    また、グループを設定すると、そのグループメンバーは参加者でなくてもそのタスクを参照できます。
    グループからコマンドを実行した場合、参加グループは実行元のグループしか指定できない。
    ■コマンド引数
    1: タスク名
    2: 期限。"年/月/日 時:分"の形式で指定。年や時間は省略可能
    (3: 重要度。「高」、「中」、「低」のいずれか。重要度によって催促の激しさが変わる)
    (4: 、か,区切りで参加者を指定。デフォルトは送信者。「全員」で関連グループ全員を指定。
    (5: 参加グループを指定。デフォルトは送信元グループ)'''
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

    # 重要度を取得
    try:
        if importance:
            task_importance = TaskImportance(importance)
        else:
            task_importance = TaskImportance.Middle
    except ValueError:
        return None, ["無効な重要度が指定された……。重要度は「高」、「中」、「低」のいずれかだよ……。"]

    new_task = Task.objects.create(
        name=task_name, deadline=task_deadline, importance=task_importance.name)
    new_task.managers.add(task_create_user)
    try:
        # 参加グループ設定
        related_group = None
        # グループが指定されていたらそれを設定
        if group_name:
            try:
                # 送信元がグループならそのグループしか指定できない
                if command_source.group_data and group_name != command_source.group_data.name:
                    new_task.delete()
                    return None, ["グループ内ではそのグループしか関連グループに指定できません。"]
                else:
                    related_group = db_util.get_group_by_name_from_database(
                        group_name)
                    new_task.group = related_group
            except GroupNotFoundError:
                new_task.delete()
                return None, ["指定されたグループ「{}」が見つりません。".format(group_name)]
        # グループが指定されていなくて送信元がグループならそれを設定
        elif command_source.group_data:
            related_group = command_source.group_data
            new_task.group = command_source.group_data
            group_name = "このグループ"
        else:
            group_name = "なし"

        # 参加者設定
        valid_participant_name_list = []

        def add_participant(user):
            '''参加者を追加する'''
            # 重複がないようにする
            if not new_task.participants.filter(id=user.id).exists():
                new_task.participants.add(user)
                valid_participant_name_list.append(user.name)
        # 全員参加が指定されたら関連グループの全メンバーを参加させる
        if participants == EVERYONE_WORD:
            if related_group:
                for member in related_group.members.all():
                    add_participant(member)
            else:
                new_task.delete()
                return None, ["参加者にグループメンバー全員が指定されたけど、グループが指定されてないよ。。。"]
        # 参加者が指定されていたらそれを設定
        elif participants:
            participant_name_list = util.split_command_paramater_strig(
                participants)
            for user_name in participant_name_list:
                try:
                    add_participant(
                        db_util.get_user_by_name_from_database(user_name))
                except UserNotFoundError:
                    error_list.append(
                        "ユーザー「{}」が見つからないため、参加者に追加できませんでした。".format(user_name))
        # 参加者が指定されていなかったら送信者を設定
        if not valid_participant_name_list:
            new_task.participants.add(task_create_user)
            valid_participant_name_list.append(task_create_user.name)
        # データベースに保存
        new_task.save()
        reply = "「{}」タスクを重要度「{}」で作成し、期限を{}に設定しました。\n".format(
            task_name, task_importance.value, util.convert_datetime_in_default_timezone_to_string(task_deadline))
        reply += "■関連グループ\n{}\n".format(group_name)
        reply += "■参加者\n{}".format("、".join(valid_participant_name_list))
        return reply, error_list
    # 途中でエラーになったら作成したタスクは削除する
    except Exception:
        new_task.delete()
        raise


@StandardMessageCommandGroup.add_command("タスク列挙", UserAuthority.Watcher)
def list_task_command(command_source: CommandSource, target: str = None, name: str = None)->(str, [str]):
    '''タスクの一覧を表示します。
    Masterユーザー、タスクの参加者、タスクの関連グループのメンバーのみ閲覧可能です。
    グループでコマンドを事項した場合は、そのグループのタスクのみ表示されます。
    ■コマンド引数
    (1: 「グループ」又は「ユーザー」。デフォルトは両方)
    (2: グループ又はユーザーの名前。デフォルトは送信者)'''
    def list_user_task(command_source: CommandSource, name: str):
        try:
            '''指定ユーザーのタスクをリストアップする'''
            user = db_util.get_user_by_name_from_database(name)
            # 送信元がグループの場合はそのグループのタスクのみに絞る
            if command_source.group_data:
                task_name_deadline_list = [(task.name, task.deadline) for task in user.belonging_tasks.filter(
                    group=command_source.group_data) if check_task_watch_authority(user, task)]
            else:
                task_name_deadline_list = [(task.name, task.deadline) for task in user.belonging_tasks.all(
                ) if check_task_watch_authority(user, task)]
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
            return None, ["グループからのコマンドじゃないのでターゲットにグループを指定しても意味ないよ。"]
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


@StandardMessageCommandGroup.add_command("タスク詳細", UserAuthority.Watcher)
def check_task_command(command_source: CommandSource, target_task_name: str)->(str, [str]):
    '''タスクの詳細を表示します。
    Masterユーザー、タスクの参加者、タスクの関連グループのメンバーのみ表示可能です。
    グループ内ではそのグループのタスクのみ表示可能です。
    ■コマンド引数
    1: タスク名又はタスク短縮名'''
    try:
        task = db_util.get_task_by_name_or_shot_name_from_database(
            target_task_name)
        # グループ内でそのグループ以外のタスクが指定されたら見つからないとする
        if command_source.group_data and task.group.id != command_source.group_data.id:
            raise TaskNotFoundError()
        # Masterユーザー、管理者、参加者、関連グループのメンバーのみ閲覧可能
        if check_task_watch_authority(command_source.user_data, task):
            reply = "<タスク詳細>\n"
            reply += "■名前\n{}\n".format(target_task_name)
            reply += "■短縮名\n{}\n".format(
                task.short_name if task.short_name else "未設定")
            reply += "■期限\n{}\n".format(
                util.convert_datetime_in_default_timezone_to_string(task.deadline))
            reply += "■重要度\n{}\n".format(TaskImportance[task.importance].value)
            # メンバー
            if task.participants.exists():
                participants_str = ",".join(
                    [participant.name for participant in task.participants.all()])
            else:
                participants_str = "なし"
            reply += "■グループ\n{}\n".format(
                task.group.name if task.group else "なし")
            reply += "■メンバー\n{}\n".format(participants_str)
            # 参加可能者
            if task.joinable_members.exists():
                joinables_str = ",".join(
                    [member.name for member in task.joinable_members.all()])
                reply += "■参加可能者\n{}\n".format(joinables_str)
            # 欠席者
            if task.absent_members.exists():
                absents_str = ",".join(
                    [member.name for member in task.absent_members.all()])
                reply += "■欠席者\n{}\n".format(absents_str)
            # 管理者
            if task.managers.exists():
                managers_str = ",".join(
                    [manager.name for manager in task.managers.all()])
            else:
                managers_str = "なし"
            reply += "■管理者\n{}".format(managers_str)
            return reply, []
        else:
            return None, ["タスクの閲覧権限がありません。タスクの閲覧はMasterユーザー、タスクの参加者、タスクの関連グループのメンバーのみ可能でーす。"]
    except TaskNotFoundError:
        return None, ["タスク「{}」が見つからない！".format(target_task_name)]


@StandardMessageCommandGroup.add_command("タスク削除", UserAuthority.Editor)
def remove_task_command(command_source: CommandSource, target_task_name)->(str, [str]):
    '''タスクを削除します。
    Masterユーザー、タスクの管理者のみ削除可能です。
    グループ内ではそのグループのタスクのみ削除可能です。
    ■コマンド引数
    1: タスク名又はタスク短縮名'''
    try:
        task = db_util.get_task_by_name_or_shot_name_from_database(
            target_task_name)
        # グループ内でそのグループ以外のタスクが指定されたら見つからないとする
        if command_source.group_data and task.group.id != command_source.group_data.id:
            raise TaskNotFoundError()
        # Masterユーザーか、そのタスクの管理者のみ削除可能
        if check_task_edit_authority(command_source.user_data, task):
            task.delete()
            disable_task_check_command_if_need(command_source)
            return "タスク「{}」を削除しました。".format(target_task_name), []
        else:
            return None, ["タスクの編集権限がありません。タスクの編集は Masterユーザー、タスクの管理者のみ可能ですー。"]
    except TaskNotFoundError:
        return None, ["タスク「{}」が見つからない！".format(target_task_name)]


@StandardMessageCommandGroup.add_command("タスク編集", UserAuthority.Editor)
def edit_task_command(command_source: CommandSource)->(str, [str]):
    '''タスクを編集をします(未実装)。
    Editor権限以上のユーザーでないとタスク管理者にはなれません。
    タスク管理者がいなくなるような変更は行えません。
    タスクの短縮名は全てタスク名、他のタスク短縮名と重複することはできません。
    Masterユーザーかタスクの管理者のみ変更可能です。
    グループ内ではそのグループのタスクしか編集できません。'''
    return None, ["未実装"]
