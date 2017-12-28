'''定期的に実行するジョブを定義したファイル'''

from apscheduler.schedulers.blocking import BlockingScheduler

@scheduler.scheduled_job('interval', minutes=1)
def timed_job():
    print("Run notifier")

scheduler.start()