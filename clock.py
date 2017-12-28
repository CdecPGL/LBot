'''定期的に実行するジョブを定義したファイル'''

from apscheduler.schedulers.blocking import BlockingScheduler
import bot.line_api as line_api


def timed_job():
    #line_api.api.push_message("", "test")
    pass


if __name__ == "__main__":
    sc = BlockingScheduler()
    sc.add_job(timed_job, "interval", seconds=30, max_instances=10)
    sc.start()
