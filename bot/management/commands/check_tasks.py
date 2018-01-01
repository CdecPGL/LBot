'''check_tasksコマンド'''

import datetime
from enum import Enum

from django.core.management.base import BaseCommand
from linebot.models import TextSendMessage

from bot import line
from bot.models import Task, TaskImportance
from bot.utilities import TIMEZONE_DEFAULT


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
                for group in task.groups.all():
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
        elif task_check_type == TaskCheckType.TommorowImportantTasksRemind:
            # 明日が期限の重要タスクを通知
            group_task_map = {}
            for task in Task.objects.filter(deadline__range=get_tommorow_range(), importance=TaskImportance.High.name):
                for group in task.groups.all():
                    if group.line_group.group_id in group_task_map:
                        group_task_map[group.line_group.group_id].append(task)
                    else:
                        group_task_map[group.line_group.group_id] = [task]

            for line_group_id, task_list in group_task_map.items():
                mess = "こんにちは。明日が期限の重要なタスクは以下のとおりだよ。"
                line.api.push_message(
                    line_group_id, TextSendMessage(text=mess))
                mess = "\n".join(
                    ["■{}(期限: {})".format(task.name, convert_deadline_to_string(task.deadline)) for task in task_list])
                line.api.push_message(
                    line_group_id, TextSendMessage(text=mess))
                mess = "おやすみなさい:D"
                line.api.push_message(
                    line_group_id, TextSendMessage(text=mess))
            pass
        elif task_check_type == TaskCheckType.TasksPreRemindAndCheck:
            pass
        else:
            assert False
