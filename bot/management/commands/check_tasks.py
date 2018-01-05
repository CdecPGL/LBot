'''check_tasksコマンド'''

from django.core.management.base import BaseCommand

from ...task_check import TaskChecker, TaskCheckType


class Command(BaseCommand):
    '''check_tasksコマンド'''
    # python manage.py help count_entryで表示されるメッセージ
    help = 'タスクの更新と告知を行う'

    def add_arguments(self, parser):
        '''コマンドライン引数を指定。
        argparseモジュールが渡される。'''
        parser.add_argument('task_check_type',
                            type=TaskCheckType, choices=list(TaskCheckType))
        parser.add_argument('-f', dest="force",
                            action="store_true", default=False)

    def handle(self, *args, **options):
        task_check_type = options["task_check_type"]
        force = options["force"] if "force" in options else False
        TaskChecker.execute(task_check_type, force)
