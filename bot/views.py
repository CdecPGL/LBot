from django.http import HttpResponse
from django.shortcuts import render

from .line import event_handlers as event_handlers


def callback(request):
    event_handlers.event_handler.handle(request.body.decode('utf-8'),
                                        request.META["HTTP_" + "X_LINE_SIGNATURE"])  # 元はX-Line-Signature
    return HttpResponse()
