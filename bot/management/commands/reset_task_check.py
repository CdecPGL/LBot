'''check_tasksコマンド'''

from django.core.management.base import BaseCommand

from ...message_commands import remove_message_command_group
from ...models import Group, Task, TaskJoinCheckJob, User


class Command(BaseCommand):
    '''check_tasksコマンド'''
    # python manage.py help count_entryで表示されるメッセージ
    help = 'タスク確認のリセットを行う。'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        # タスクの確認フラグリセット
        Task.objects.update(is_tomorrow_check_finished=False,
                            is_tomorrow_remind_finished=False, is_soon_check_finished=False)
        # タスク確認ジョブの削除
        TaskJoinCheckJob.objects.all().delete()
        # タスク参加確認コマンドを無効化
        for user in User.objects.all():
            remove_message_command_group(user, "タスク参加確認")
        for group in Group.objects.all():
            remove_message_command_group(group, "タスク参加確認")
