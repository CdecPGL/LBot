'''タスク確認時コマンド'''

import sys

from ...authorities import UserAuthority
from ...models import TaskJoinCheckJob, User
from ...utilities import split_command_paramater_strig
from ..message_command import (CommandSource, MessageCommandGroupBase,
                               remove_message_command_group)


class CheckTaskMessageCommandGroup(MessageCommandGroupBase):
    '''標準のメッセージコマンドグループ'''
    name = "タスク参加確認"
    order = 50
    validate_in_initialize = False
    enable_command_suggestion = True
    enable_auto_command_correction = True
    suggestion_word_match_rate_threshold = 0.8


def set_user_participate_state(user: User, task_check_job: TaskJoinCheckJob, is_participate: bool):
    '''ユーザーのタスク参加状態を設定する'''
    task = task_check_job.task
    if not task.participants.filter(id=user.id):
        return False, "あなたはタスク「{}」のメンバーじゃないよ。。。".format(task.name)
    if is_participate:
        # 参加登録されていなかったらする
        task.joinable_members.add(user)
        # 欠席登録されていたら除去
        try:
            task.absent_members.remove(task.absent_members.get(id=user.id))
        except User.DoesNotExist:
            pass
    else:
        # 欠席登録されていなかったらする
        task.absent_members.add(user)
        # 参加登録されていたら除去
        try:
            task.joinable_members.remove(task.joinable_members.get(id=user.id))
        except User.DoesNotExist:
            pass
    # データベースの変更を保存
    task.save()
    # はじめての確認なら確認済みユーザーに追加
    task_check_job.checked_users.add(user)

    # 全員の参加確認が済んでいたらそのタスク確認ジョブを削除してメッセージを出力
    if task_check_job.checked_users.count() == task.participants.count():
        task_check_job.delete()
        reply = "タスク「{}」の参加確認が完了しました。\n".format(task.name)
        # 参加可能者
        if task.joinable_members.exists():
            joinable_str = "、".join(
                [joinable.name for joinable in task.joinable_members.all()])
        else:
            joinable_str = "なし"
        reply += "<参加可能者>\n{}\n".format(joinable_str)
        # 欠席者
        if task.absent_members.exists():
            absent_str = "、".join(
                [absent.name for absent in task.absent_members.all()])
        else:
            absent_str = "なし"
        reply += "<欠席者>\n{}".format(absent_str)
        return True, reply
    else:
        task_check_job.save()
        return True, None


def set_participate_state(command_source: CommandSource, target_check_number_or_name: str, is_participate: bool)->(str, [str]):
    '''タスクへの参加不参加を設定する'''
    # コマンドが実行できるかどうか確認
    if not command_source.group_data:
        remove_message_command_group(command_source.user_data, "タスク参加確認")
        return None, ["グループ外での実行には対応していません。"]
    checking_tasks = TaskJoinCheckJob.objects.filter(
        group=command_source.group_data)
    if not checking_tasks.exists():
        remove_message_command_group(command_source.group_data, "タスク参加確認")
        return "このグループで現在確認中のタスクはありません。", []

    # 対象のタスク確認を取得
    checking_task_str_list = ["{}: {}".format(check_task.check_number, check_task.task.name) for check_task in sorted(
        checking_tasks.all(), key=lambda check_task: check_task.check_number)]
    # 番号が指定されている場合は、指定番号の確認中タスクを探す
    if target_check_number_or_name:
        try:
            target_check_number_or_name_list = split_command_paramater_strig(
                target_check_number_or_name)
            target_checking_task_list = checking_tasks.filter(
                check_number__in=target_check_number_or_name_list)
        except (TaskJoinCheckJob.DoesNotExist, ValueError):
            # 番号で当てはまらなかったらタスク名で試行する
            try:
                target_checking_task_list = checking_tasks.filter(
                    task__name__in=target_check_number_or_name_list)
            except TaskJoinCheckJob.DoesNotExist:
                return None, ["指定番号又は名前の確認中タスクは存在しないよ。\n{}".format("\n".join(checking_task_str_list))]
    else:
        # 番号が指定されていない場合、確認中タスクが一つならそれを対象にする
        try:
            target_checking_task_list = [checking_tasks.get()]
        except TaskJoinCheckJob.DoesNotExist:
            sys.stderr.write("グループ「{}」のタスク確認ジョブ(checking_tasks)が存在しません。\n".format(
                command_source.group_data.name))
            return None, ["内部エラー(タスク確認ジョブが存在しない)"]
        except TaskJoinCheckJob.MultipleObjectsReturned:
            return None, ["確認対象のタスクが複数あるので、番号で指定してね。\n{}".format("\n".join(checking_task_str_list))]

    # 参加登録を行う
    user = command_source.user_data
    suceeded_task_list = []
    error_list = []
    mess_list = []
    for task_check in target_checking_task_list:
        is_suceed, mess = set_user_participate_state(
            user, task_check, is_participate)
        if is_suceed:
            suceeded_task_list.append(task_check.task)
            if mess:
                mess_list.append(mess)
        else:
            if mess:
                error_list.append(mess)

    # タスク確認ジョブがなくなったらタスクの確認を終了する
    if not TaskJoinCheckJob.objects.filter(group=command_source.group_data).exists():
        remove_message_command_group(command_source.group_data, "タスク参加確認")

    # 返信を生成
    if suceeded_task_list:
        reply = "すっごーい！キミは{}に{}するフレンズなんだね！".format("".join(["「{}」".format(
            task.name) for task in suceeded_task_list]), "参加" if is_participate else "欠席")
        if mess_list:
            reply += "\n\n"
            reply += "\n\n".join(mess_list)
    else:
        reply = None
    return reply, error_list


@CheckTaskMessageCommandGroup.add_command("できる", UserAuthority.Watcher)
def participate_command(command_source: CommandSource, target_task_number: str=None)->(str, [str]):
    '''タスクに参加できることを伝えます。
    ■コマンド引数
    (1: 対象の確認番号かタスク名。,か、区切りで複数指定可能。対象タスクが一つしかない場合は省略可能)'''
    return set_participate_state(command_source, target_task_number, True)


@CheckTaskMessageCommandGroup.add_command("できない", UserAuthority.Watcher)
def absent_command(command_source: CommandSource, target_task_number: str=None):
    '''タスクに参加できないことを伝えます。
    ■コマンド引数
    (1: 対象の確認番号かタスク名。,か、区切りで複数指定可能。対象タスクが一つしかない場合は省略可能)'''
    return set_participate_state(command_source, target_task_number, False)


@CheckTaskMessageCommandGroup.add_command("確認状況", UserAuthority.Watcher)
def display_task_check_job_command(command_source: CommandSource):
    '''タスク参加確認の状況を表示します。'''
    if not command_source.group_data:
        remove_message_command_group(command_source.user_data, "タスク参加確認")
        return None, ["グループ外での実行には対応していません。"]

    checking_tasks = TaskJoinCheckJob.objects.filter(
        group=command_source.group_data)
    if not checking_tasks.exists():
        remove_message_command_group(command_source.group_data, "タスク参加確認")
        return "このグループで現在確認中のタスクはありません。", []

    reply = "このグループでのタスク参加確認状況は以下のとおりです。\n"
    for task_check in checking_tasks:
        task = task_check.task
        reply += "<{}>\n".format(task.name)
        for member in task.participants.all():
            norepliers = []
            if not task.joinable_members.filter(id=member.id).exists() and not task.absent_members.filter(id=member.id).exists():
                norepliers.append(member)
            if norepliers:
                reply += "■未返信: {}\n".format(
                    ",".join([user.name for user in norepliers]))
            if task.joinable_members.exists():
                reply += "■参加可能: {}\n".format(
                    ",".join([user.name for user in task.joinable_members.all()]))
            if task.absent_members.exists():
                reply += "■欠席: {}\n".format(
                    ",".join([user.name for user in task.absent_members.all()]))
        reply.rstrip("\n")
    return reply, []
