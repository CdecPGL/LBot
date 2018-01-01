'''定期的に実行するジョブを定義したファイル'''

from datetime import timezone

from apscheduler.schedulers.blocking import BlockingScheduler
from django.core.management import call_command

import bot.line_api as line_api
from bot.management.commands.check_tasks import TaskCheckType
from bot.utilities import get_datetime_with_jst


def tommorow_tasks_remind_job():
    '''明日のタスクのリマインドを行うジョブ'''
    call_command("check_tasks", TaskCheckType.TommorowTasksRemind)


def tommorow_important_tasks_check_job():
    '''明日の重要タスクの確認を行うジョブ'''
    call_command("check_tasks", TaskCheckType.TommorowTasksRemind)


def important_tasks_pre_check_job():
    '''重要タスクの事前確認を行うジョブ'''
    call_command("check_tasks", TaskCheckType.ImportantTasksPreCheck)


if __name__ == "__main__":
    sc = BlockingScheduler()
    # 明日のタスク確認(毎日23:00に確認)
    tommorow_remind_datetime = get_datetime_with_jst(
        2000, 1, 1, 23).astimezone(timezone('UTC'))
    sc.add_job(tommorow_tasks_remind_job, "cron", hour=tommorow_remind_datetime.hour,
               minute=tommorow_remind_datetime.minute)
    # 明日の重要タスク確認(毎日12:00に確認)
    tommorow_important_check_datetime = get_datetime_with_jst(
        2000, 1, 1, 12).astimezone(timezone('UTC'))
    sc.add_job(tommorow_important_tasks_check_job, "cron", hour=tommorow_important_check_datetime.hour,
               minute=tommorow_important_check_datetime.minute)
    # 重要タスクの事前確認(10分おきに確認)
    sc.add_job(important_tasks_pre_check_job, "interval", minute=10)
    sc.start()
