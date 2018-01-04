from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from django.apps import AppConfig
from django.core.management import call_command

from bot.management.commands.check_tasks import TaskCheckType
from bot.utilities import TIMEZONE_DEFAULT


def test_job():
    print("testsetsetsets")

def tommorow_tasks_remind_job():
    '''明日のタスクのリマインドを行うジョブ'''
    call_command("check_tasks", TaskCheckType.TommorowTasksRemind)


def tommorow_important_tasks_check_job():
    '''明日の重要タスクの確認を行うジョブ'''
    call_command("check_tasks", TaskCheckType.TommorowImportantTasksCheck)


def important_tasks_pre_check_job():
    '''タスクの事前確認とリマインドを行うジョブ'''
    print("tsetsetsetsetset")
    call_command("check_tasks", TaskCheckType.TasksPreRemindAndCheck)

class BotConfig(AppConfig):
    name = 'bot'

    def ready(self):
        '''アプリ起動時の処理'''
        print("初期化。")
        scheduler = BackgroundScheduler()
        # # 明日のタスク確認(毎日23:00に確認)
        # tommorow_remind_datetime = datetime(
        #     2000, 1, 1, 23, tzinfo=TIMEZONE_DEFAULT).astimezone(timezone.utc)
        # scheduler.add_job(tommorow_tasks_remind_job, "cron", hour=tommorow_remind_datetime.hour,
        #            minute=tommorow_remind_datetime.minute)
        # # 明日の重要タスク確認(毎日12:00に確認)
        # tommorow_important_check_datetime = datetime(
        #     2000, 1, 1, 12, tzinfo=TIMEZONE_DEFAULT).astimezone(timezone.utc)
        # scheduler.add_job(tommorow_important_tasks_check_job, "cron", hour=tommorow_important_check_datetime.hour,
        #            minute=tommorow_important_check_datetime.minute)
        # タスクの事前確認(10分おきに確認)
        scheduler.add_job(important_tasks_pre_check_job, "interval", minutes=1)

        scheduler.start()
