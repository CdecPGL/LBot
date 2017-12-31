'''check_tasksコマンド'''

from django.core.management.base import BaseCommand
from linebot.models import TextSendMessage

from bot import line
from bot.models import Task
import datetime


class Command(BaseCommand):
    '''check_tasksコマンド'''
    # python manage.py help count_entryで表示されるメッセージ
    help = 'タスクの更新と告知を行う'

    def add_arguments(self, parser):
        '''コマンドライン引数を指定。
        argparseモジュールが渡される。'''
        pass

    def handle(self, *args, **options):
        # 明日が期限のタスクを通知
        group_task_map = {}
        today = datetime.date.today()
        start_datetime = datetime.datetime(
            today.year, today.month, today.day, 0, 0, 0)
        end_datetime = datetime.datetime(
            today.year, today.month, today.day, 23, 59, 59, 999999)
        for task in Task.objects.filter(deadline__range=(start_datetime, end_datetime)):
            for group in task.groups.all():
                if group.line_group.group_id in group_task_map:
                    group_task_map[group.line_group.group_id].append(task.name)
                else:
                    group_task_map[group.line_group.group_id] = [task.name]

        for line_group_id, task_name_list in group_task_map.items():
            mess = "こんばんは。明日が期限のタスクは以下のとおりだよ。"
            line.api.push_message(line_group_id, TextSendMessage(text=mess))
            mess = "\n".join(task_name_list)
            line.api.push_message(line_group_id, TextSendMessage(text=mess))
            mess = "おやすみ:D"
            line.api.push_message(line_group_id, TextSendMessage(text=mess))
