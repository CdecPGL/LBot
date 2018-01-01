'''check_tasksコマンド'''

import datetime
from enum import Enum, auto

from django.core.management.base import BaseCommand
from linebot.models import TextSendMessage

from bot import line
from bot.models import Task

from bot.utilities import get_datetime_with_jst


class TaskCheckType(Enum):
    # 明日のタスクのリマインド
    TommorowTasksRemind = "TommorowTasksRemind"
    # 明日の重要タスクの確認
    TommorowImportantTasksCheck = "TommorowImportantTasksCheck"
    # 重要タスクの事前確認
    ImportantTasksPreCheck = "ImportantTasksPreCheck"


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
            tommorow = datetime.date.today() + datetime.timedelta(days=1)
            start_datetime = get_datetime_with_jst(
                tommorow.year, tommorow.month, tommorow.day, 0, 0, 0)
            end_datetime = get_datetime_with_jst(
                tommorow.year, tommorow.month, tommorow.day, 23, 59, 59, 999999)
            for task in Task.objects.filter(deadline__range=(start_datetime, end_datetime)):
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
                    ["■{}({})".format(task.name, task.deadline.time()) for task in task_list])
                line.api.push_message(
                    line_group_id, TextSendMessage(text=mess))
                mess = "おやすみなさい:D"
                line.api.push_message(
                    line_group_id, TextSendMessage(text=mess))
        elif task_check_type == TaskCheckType.TommorowImportantTasksRemind:
            pass
        elif task_check_type == TaskCheckType.ImportantTasksPreCheck:
            pass
        else:
            assert False
