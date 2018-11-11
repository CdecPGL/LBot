from django.http import HttpResponse
from django.shortcuts import render


def callback(request):
    line_signeture_key = "HTTP_" + "X_LINE_SIGNATURE"  # 元はX-Line-Signature
    # LINEからのリクエストの場合
    from .line.event_handlers import event_handler as line_event_handelr
    if line_signeture_key in request.META:
        line_event_handelr.handle(request.body.decode(
            'utf-8'), request.META[line_signeture_key])
    return HttpResponse()
