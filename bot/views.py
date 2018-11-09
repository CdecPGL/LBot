from django.http import HttpResponse
from django.shortcuts import render

from .line import event_handlers as event_handlers


def callback(request):
    line_signeture_key = "HTTP_" + "X_LINE_SIGNATURE"  # 元はX-Line-Signature
    # LINEからのリクエストの場合
    if line_signeture_key in request.META:
        event_handlers.event_handler.handle(request.body.decode(
            'utf-8'), request.META[line_signeture_key])
    return HttpResponse()
