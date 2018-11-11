from .event_handlers import register_event_handlers
from .settings import set_up_line


def start_line_client():
    '''LINEクライアントを開始する。'''
    set_up_line()
    register_event_handlers()
