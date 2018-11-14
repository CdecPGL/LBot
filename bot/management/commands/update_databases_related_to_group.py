'''update_databases_related_to_groupコマンド'''

import sys

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from bot.utilities import ServiceGroupKind

from ...models import Group, ServiceGroup


class Command(BaseCommand):
    '''update_databases_related_to_groupコマンド'''
    # python manage.py help count_entryで表示されるメッセージ
    help = '古いグループに関するデータベースを新しいものに更新する'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        for group in Group.objects.all():
            if group.line_group:
                kind = ServiceGroupKind.LINEGroup.name
                if ServiceGroup.objects.filter(kind=kind, id_in_service=group.line_group.group_id).exists():
                    sys.stderr.write("サービスグループは一つのグループにしか所属できません。\n")
                else:
                    service_group = ServiceGroup.objects.create(
                        kind=kind, id_in_service=group.line_group.group_id)
                    service_group.belonging_group = group
                    service_group.save()
            if group.discord_server:
                kind = ServiceGroupKind.DiscordServer.name
                if ServiceGroup.objects.filter(kind=kind, id_in_service=group.discord_server.server_id).exists():
                    sys.stderr.write("サービスグループは一つのグループにしか所属できません。\n")
                else:
                    service_group = ServiceGroup.objects.create(
                        kind=kind, id_in_service=group.discord_server.server_id)
                    service_group.belonging_group = group
                    service_group.save()
