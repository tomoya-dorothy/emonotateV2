import os
import json

from importlib import import_module

from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse
from django.shortcuts import render, redirect

from lazysignup.decorators import allow_lazy_user

from django.http import JsonResponse

from users.serializers import UserSerializer

User = get_user_model()

@allow_lazy_user
def index(request):
    content = ""
    #--------
    # * APIとして利用する際には上側を使用
    #--------
    # return JsonResponse(UserSerializer().data, status=200)

    #--------
    # frontend として使用する際には下側を使用
    #--------
    module = import_module(os.environ.get('DJANGO_SETTINGS_MODULE'))
    response = redirect(module.APPLICATION_URL)
    response.set_cookie("username", request.user.username)
    response.set_cookie("userid", request.user.id)
    response.set_cookie("groups", ','.join(
        list(map(lambda obj: obj.name, request.user.groups.all()))))
    return response


@login_required
def app(request):
    context = {
        'permissions': json.dumps(list(request.user.get_all_permissions())),
        'YOUTUBE_API_KEY': os.environ.get('YOUTUBE_API_KEY')
    }

    template = 'backend/app.html'
    return render(request, template, context)
