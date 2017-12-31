'''check_tasksコマンド'''

from django.core.management.base import BaseCommand

from bot import line
from bot.models import Task


class Command(BaseCommand):
    '''check_tasksコマンド'''
    # python manage.py help count_entryで表示されるメッセージ
    help = 'タスクの更新と告知を行う'

    def add_arguments(self, parser):
        '''コマンドライン引数を指定。
        argparseモジュールが渡される。'''
        pass

    def handle(self, *args, **options):
        group_task_map = {}
        for task in Task.objects.all():
            for group in task.groups.all():
                if group.line_group.group_id in group_task_map:
                    group_task_map[group.line_group.group_id].append(task.name)
                else:
                    group_task_map[group.line_group.group_id] = [task.name]

        for line_group_id, task_name_list in group_task_map.items():
            mess = "プッシュメッセージテスト\n"
            mess += ".\n".join(task_name_list)
            line.api.push_message(line_group_id, mess)
