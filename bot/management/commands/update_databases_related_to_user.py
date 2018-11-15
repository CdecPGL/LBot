'''update_databases_related_to_userコマンド'''

import sys

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from bot.utilities import ServiceUserKind

from ...models import ServiceUser, User


class Command(BaseCommand):
    '''update_databases_related_to_userコマンド'''
    # python manage.py help count_entryで表示されるメッセージ
    help = '古いユーザーに関するデータベースを新しいものに更新する'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for user in User.objects.all():
            if user.line_user:
                kind = ServiceUserKind.LINEUser.name
                if ServiceUser.objects.filter(kind=kind, id_in_service=user.line_user.user_id).exists():
                    sys.stderr.write("サービスグユーザーは一つのユーザーにしか所属できません。\n")
                else:
                    service_user = ServiceUser.objects.create(
                        kind=kind, id_in_service=user.line_user.user_id, name_in_service=user.line_user.name)
                    service_user.belonging_user = user
                    service_user.save()
            if user.discord_user:
                kind = ServiceUserKind.DiscordUser.name
                if ServiceUser.objects.filter(kind=kind, id_in_service=user.discord_user.user_id).exists():
                    sys.stderr.write("サービスユーザーは一つのユーザーにしか所属できません。\n")
                else:
                    service_user = ServiceUser.objects.create(
                        kind=kind, id_in_service=user.discord_user.user_id, name_in_service=user.discord_user.name)
                    service_user.belonging_user = user
                    service_user.save()
