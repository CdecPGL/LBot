'''タスク確認時コマンド'''

import sys

from bot.authorities import UserAuthority
from bot.models import TaskJoinCheckJob, User
from bot.utilities import remove_from_comma_separeted_string

from ..message_command import CommandSource, MessageCommandGroupBase


class CheckTaskMessageCommandGroup(MessageCommandGroupBase):
    '''標準のメッセージコマンドグループ'''
    name = "タスク参加確認"
    order = 50
    validate_in_initialize = False
    enable_command_suggestion = True
    enable_auto_command_correction = True
    suggestion_word_match_rate_threshold = 0.8


def set_participate_state(command_source: CommandSource, target_task_number: str, is_participate: bool)->(str, [str]):
    '''タスクへの参加不参加を設定する'''
    # コマンドが実行できるかどうか確認
    if not command_source.group_data:
        command_source.group_data.valid_message_command_groups = remove_from_comma_separeted_string(
            command_source.group_data.valid_message_command_groups, "タスク参加確認")
        command_source.group_data.save()
        return None, ["グループ外での実行には対応していません。"]
    checking_tasks = TaskJoinCheckJob.objects.filter(
        group=command_source.group_data)
    if not checking_tasks:
        command_source.user_data.valid_message_command_groups = remove_from_comma_separeted_string(
            command_source.user_data.valid_message_command_groups, "タスク参加確認")
        command_source.user_data.save()
        return "このグループで現在確認中のタスクはありません。", []

    # 対象のタスク確認を取得
    checking_task_list = ["{}: {}".format(check_task.check_number, check_task.task.name) for check_task in sorted(
        checking_tasks.all(), key=lambda check_task: check_task.check_number)]
    # 番号が指定されている場合は、指定番号の確認中タスクを探す
    if target_task_number:
        try:
            target_check_task = checking_tasks.get(
                check_number=target_task_number)
        except TaskJoinCheckJob.DoesNotExist:
            return None, ["指定番号の確認中タスクは存在しないよ。\n{}".format("\n".join(checking_task_list))]
        except TaskJoinCheckJob.MultipleObjectsReturned:
            sys.stderr.write("グループ「{}」のタスク確認ジョブで確認番号「{}」の重複が有ります。\n".format(
                command_source.group_data.name, target_task_number))
            return None, ["内部エラー(タスク確認ジョブの確認番号重複)"]
    else:
        # 番号が指定されていない場合、確認中タスクが一つならそれを対象にする
        try:
            target_check_task = checking_tasks.get()
        except TaskJoinCheckJob.DoesNotExist:
            sys.stderr.write("グループ「{}」のタスク確認ジョブ(checking_tasks)が存在しません。\n".format(
                command_source.group_data.name))
            return None, ["内部エラー(タスク確認ジョブが存在しない)"]
        except TaskJoinCheckJob.MultipleObjectsReturned:
            return None, ["確認対象のタスクが複数あるので、番号で指定してね。\n{}".format("\n".join(checking_task_list))]

    # 参加登録を行う
    user = command_source.user_data
    task = target_check_task.task
    # 対象タスクのメンバーではない
    if not task.participants.filter(id=user.id).exists():
        return None, ["あなたはタスク「{}」のメンバーじゃないよ。。。".format(task.name)]
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
    target_check_task.checked_users.add(user)
    # 全員の確認が取れていたら確認を終了
    if task.participants.count() == target_check_task.checked_users.count():
        target_check_task.delete()
        # 最後の確認タスクだったら、タスクの確認を終了する
        if len(checking_task_list) == 1:
            command_source.group_data.valid_message_command_groups = remove_from_comma_separeted_string(
                command_source.group_data.valid_message_command_groups, "タスク参加確認")
            command_source.group_data.save()
            reply = "「{}」に{}するんだね。了解！".format(
                task.name, "参加" if is_participate else "欠席")
            reply += "\nタスク「{}」の参加確認が完了しました。\n"
            reply += "<参加可能者>\n{}\n".join(
                "、".join([joinable.name for joinable in task.joinable_members.all()]))
            reply += "<欠席者>\n{}".join(
                "、".join([absent.name for absent in task.absent_members.all()]))
            return reply, []
    else:
        target_check_task.save()
        return "「{}」に{}するんだね。了解！".format(task.name, "参加" if is_participate else "欠席"), []


@CheckTaskMessageCommandGroup.add_command("できる", UserAuthority.Watcher)
def participate_command(command_source: CommandSource, target_task_number: str=None)->(str, [str]):
    '''タスクに参加できることを伝えます。
    ■コマンド引数
    (1: 対象のタスク番号。対象タスクが一つしかない場合は省略可能)'''
    return set_participate_state(command_source, target_task_number, True)


@CheckTaskMessageCommandGroup.add_command("できない", UserAuthority.Watcher)
def absent_command(command_source: CommandSource, target_task_number: str=None):
    '''タスクに参加できないことを伝えます。
    ■コマンド引数
    (1: 対象のタスク番号。対象タスクが一つしかない場合は省略可能)'''
    return set_participate_state(command_source, target_task_number, False)
