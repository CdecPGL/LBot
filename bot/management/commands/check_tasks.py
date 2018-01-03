'''check_tasksコマンド'''

import datetime
from enum import Enum

from django.core.management.base import BaseCommand
from linebot.models import TextSendMessage

from bot import line
from bot.models import Task, TaskImportance, TaskJoinCheckJob
from bot.utilities import TIMEZONE_DEFAULT, add_to_comma_separeted_string


def convert_deadline_to_string(deadline):
    '''期限を時間分の文字列に変換'''
    deadline = deadline.astimezone(TIMEZONE_DEFAULT)
    return "{:02d}:{:02d}".format(deadline.hour, deadline.minute)


def get_tommorow_range():
    '''明日の日時範囲を取得する'''
    tommorow = datetime.date.today() + datetime.timedelta(days=1)
    start_datetime = datetime.datetime(
        tommorow.year, tommorow.month, tommorow.day, 0, 0, 0, tzinfo=TIMEZONE_DEFAULT)
    end_datetime = datetime.datetime(
        tommorow.year, tommorow.month, tommorow.day, 23, 59, 59, 999999, tzinfo=TIMEZONE_DEFAULT)
    return start_datetime, end_datetime


class TaskCheckType(Enum):
    '''タスクチェックのタイプ'''
    # 明日のタスクのリマインド
    TommorowTasksRemind = "TommorowTasksRemind"
    # 明日の重要タスクの確認
    TommorowImportantTasksCheck = "TommorowImportantTasksCheck"
    # タスクの事前確認とリマインド
    TasksPreRemindAndCheck = "TasksPreRemindAndCheck"


class Command(BaseCommand):
    '''check_tasksコマンド'''
    # python manage.py help count_entryで表示されるメッセージ
    help = 'タスクの更新と告知を行う'

    def add_arguments(self, parser):
        '''コマンドライン引数を指定。
        argparseモジュールが渡される。'''
        parser.add_argument('task_check_type',
                            type=TaskCheckType, choices=list(TaskCheckType))

    def handle(self, *args, **options):
        task_check_type = options["task_check_type"]

        if task_check_type == TaskCheckType.TommorowTasksRemind:
            # 明日が期限のタスクを通知
            group_task_map = {}
            for task in Task.objects.filter(deadline__range=get_tommorow_range()):
                group = task.group
                if group.line_group.group_id in group_task_map:
                    group_task_map[group.line_group.group_id].append(task)
                else:
                    group_task_map[group.line_group.group_id] = [task]

            for line_group_id, task_list in group_task_map.items():
                mess = "こんばんは。明日が期限のタスクは以下のとおりだよ。"
                line.api.push_message(
                    line_group_id, TextSendMessage(text=mess))
                mess = "\n".join(
                    ["■{}(期限: {})".format(task.name, convert_deadline_to_string(task.deadline)) for task in task_list])
                line.api.push_message(
                    line_group_id, TextSendMessage(text=mess))
                mess = "おやすみなさい:D"
                line.api.push_message(
                    line_group_id, TextSendMessage(text=mess))
        elif task_check_type == TaskCheckType.TommorowImportantTasksCheck:
            # 明日が期限の重要タスクを通知(グループのみ)
            group_task_map = {}
            for task in Task.objects.filter(deadline__range=get_tommorow_range(), importance=TaskImportance.High.name, group__isnull=False):
                group = task.group
                if group.line_group.group_id in group_task_map:
                    group_task_map[group.line_group.group_id].append(task)
                else:
                    group_task_map[group.line_group.group_id] = [task]

            for line_group_id, task_list in group_task_map.items():
                group = line.utilities.get_group_by_line_group_id_from_database(
                    line_group_id)
                # 確認タスクを追加
                check_number_count = 1
                for task in task_list:
                    task_check = TaskJoinCheckJob.objects.filter(task=task)
                    # すでに登録されていたら飛ばす
                    if not task_check.exists():
                        # 空いている確認番号を探す
                        while TaskJoinCheckJob.objects.filter(check_number=check_number_count).exists():
                            check_number_count += 1
                        # タスク確認の登録(テストで期限を12時間後にする)
                        TaskJoinCheckJob.objects.create(
                            group=task.group, task=task, check_number=check_number_count, deadline=datetime.datetime.now() + datetime.timedelta(hours=12))

                # 確認タスク一覧を作成
                important_checking_tasks = TaskJoinCheckJob.objects.filter(
                    group=group, task__importance=TaskImportance.High.name)
                ordered_checking_task_list = [check_task for check_task in sorted(
                    important_checking_tasks.all(), key=lambda check_task: check_task.check_number)]

                # 通知
                if len(ordered_checking_task_list) == 1:
                    check_task = ordered_checking_task_list[0]
                    task = check_task.task
                    mess = "こんにちは。\n重要なタスク「{}」が明日の{}からあるよ。".format(
                        task.name, convert_deadline_to_string(task.deadline))
                    line.api.push_message(
                        line_group_id, TextSendMessage(text=mess))
                    mess = "メンバーは{}。".format(
                        "".join(["「{}」".format(member.name) for member in task.participants.all()]))
                    line.api.push_message(
                        line_group_id, TextSendMessage(text=mess))
                    mess = "メンバーはこのタスクに参加できる？"
                    line.api.push_message(
                        line_group_id, TextSendMessage(text=mess))
                    mess = "参加できるなら「#できる」、できないなら「#できない」と答えてね。"
                    line.api.push_message(
                        line_group_id, TextSendMessage(text=mess))
                else:
                    mess = "こんにちは。明日が期限の重要なタスクは以下のとおりだよ。"
                    line.api.push_message(
                        line_group_id, TextSendMessage(text=mess))
                    mess = "\n".join(
                        ["{}. {}(期限: {})".format(check_task.check_number, check_task.task.name, convert_deadline_to_string(check_task.task.deadline)) for check_task in ordered_checking_task_list])
                    line.api.push_message(
                        line_group_id, TextSendMessage(text=mess))
                    mess = "これらのタスクに参加できるかできないか答えてね。"
                    line.api.push_message(
                        line_group_id, TextSendMessage(text=mess))
                    mess = "例えば、1番のタスクに参加できて2番はできない場合は\n\n#できる\n1\n#できない\n2\n\nのように答えてね。"
                    line.api.push_message(
                        line_group_id, TextSendMessage(text=mess))

                # タスク参加確認を開始
                group.valid_message_command_groups = add_to_comma_separeted_string(
                    group.valid_message_command_groups, "タスク参加確認")
                group.save()
        elif task_check_type == TaskCheckType.TasksPreRemindAndCheck:
            pass
        else:
            assert False
