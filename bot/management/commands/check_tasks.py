'''check_tasksコマンド'''

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    '''check_tasksコマンド'''
    # python manage.py help count_entryで表示されるメッセージ
    help = 'タスクの更新と告知を行う'

    def add_arguments(self, parser):
        '''コマンドライン引数を指定。
        argparseモジュールが渡される。'''
        pass

    def handle(self, *args, **options):
        pass
