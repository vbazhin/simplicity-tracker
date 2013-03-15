#author: v.bazhin
#coding: utf-8

import datetime

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django import forms
from markitup.widgets import MarkItUpWidget
from django.contrib.auth.models import User

from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.contrib import auth

from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext as _

from desk.models import Trad, Comment, InviteLink





# Вспомогательные функции (не возвращают HttpResponse, но участвуют в сборке view)
def all(request):
    all_except_me = User.objects.exclude(id=request.user.id)
    return all_except_me


def count_issues(request): # Считаем задания с разными статусами
    iss_num = lambda x: Trad.objects.filter(receiver=request.user, status=x).count() + Trad.objects.filter(
        receiver=None, status=x).exclude(author=request.user).count()
    # Те задания, которые направлены мне, либо общие, исключая те, автор которых - я
    for_check = Trad.objects.filter(author=request.user, status='done').count() # Задания направленные мне на проверку
    return iss_num('new'), iss_num('taken'), for_check, iss_num('done')


def get_tomorrow():
    today_dt = datetime.date.today()
    tomorrow_dt = today_dt + datetime.timedelta(days=1)
    tomorrow = tomorrow_dt.isoformat()
    return tomorrow

# Далее идут вьюшки

def logout(request):
    auth.logout(request)
    # Перенаправление на страницу.
    return HttpResponseRedirect("/")


def login(request):
    auth.login(request)
    # Перенаправление на страницу.
    return HttpResponseRedirect("/")


def filter_issues(fltr, request_user):
    if fltr == 'all':
        trads = list(Trad.objects.filter(receiver=request_user).exclude(status='deleted'))
        trads += list(Trad.objects.filter(receiver=None).exclude(author=request_user).exclude(status='deleted'))

        trads += list(Trad.objects.filter(author=request_user).exclude(status='deleted'))
        trads = sorted(trads, key=lambda trad: trad.given)
        #Делаю list, а не queryset т.к. при совместном запрсое разможножает объекты, созданные request.user, упорядочиваю
    elif fltr == 'current':
        trads = Trad.objects.filter(receiver=request_user, status='new') | Trad.objects.filter(receiver=request_user,
                                                                                               status='taken') | Trad.objects.filter(
            receiver=request_user, status='done') | Trad.objects.filter(receiver=None,
                                                                        status='new') | Trad.objects.filter(
            receiver=None, status='taken') | Trad.objects.filter(receiver=None, status='done')
        trads = trads.exclude(author=request_user)
    elif fltr == 'check':
        trads = Trad.objects.filter(author=request_user, status='done')
    elif fltr == 'givenbyme':
        trads = Trad.objects.filter(author=request_user).exclude(status='deleted')
    elif fltr == 'error':
        trads = Trad.objects.filter(receiver=request_user, status='error') | Trad.objects.filter(receiver=None,
                                                                                                 status='error') | Trad.objects.filter(
            author=request_user, status='error')
    elif fltr == 'new':
        trads = Trad.objects.filter(receiver=request_user, status='new').exclude(
            author=request_user) | Trad.objects.filter(receiver=None, status=fltr).exclude(author=request_user)
    else:
        trads = Trad.objects.filter(receiver=request_user, status=fltr) | Trad.objects.filter(receiver=None,
                                                                                              status=fltr)
    for trad in trads:
        trad.comments_num = Comment.objects.filter(trad=trad).count() # Cчитаем комментарии
        trad.define_condition()

    return trads


@login_required
def index(request, fltr='all', add_task=None): # Фильтруем по статусу
    new_num, taken_num, check_num, oncheck_num = count_issues(request)
    # Добавляем задание
    trads = filter_issues(fltr, request.user)
    if request.method == 'POST': # Если сабмичена форма добавления сообщений
        form = TradForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            trad = Trad()
            trad.add(cd, request.user)
            return HttpResponseRedirect("/")
    else:
        form = TradForm()
        form.fields['receiver'].queryset = User.objects.exclude(
            id=request.user.id) # Нормальный ход (все польщователи кроме меня)
    return render_to_response('index.html',
                              {'trads': trads, 'form': form, 'user': request.user, 'tomorrow': get_tomorrow(),
                               'new_num': new_num, 'taken_num': taken_num, 'check_num': check_num,
                               'oncheck_num': oncheck_num, 'page_type': 'index', 'add_task': add_task}
    )


def show_trad(request, related_trad, user_status='group_task_receiver'):
    trad = Trad.objects.get(pk=related_trad)
    if trad.status != 'deleted':
        trad.count_comments()
        trad.define_condition()
        new_num, taken_num, check_num, oncheck_num = count_issues(request)
        comments = Comment.objects.filter(trad=trad).order_by('date')
        for comment in comments:
            if comment.type == 'status_cmt':
                comment.get_text()
        if request.user in trad.receiver.all():
            user_status = 'receiver'
        if request.user == trad.author:
            user_status = 'author'
            # escape - html символы
        if request.method == 'POST':
            if 'comment' in request.POST:
                form = CommentForm(request.POST)
                if form.is_valid():
                    cd = form.cleaned_data
                    comment = Comment()
                    if len(cd['text']) > 0:
                        comment.add(cd, request.user, trad.id)
            else:
                status = [key for key in request.POST]
                trad.renew_status(status[0], request.user) # Новый статус (объеденить метод с комментированием)
            return HttpResponseRedirect("")
        else:
            form = CommentForm()
        return render_to_response('issue_page.html', {'form': form, 'user': request.user, 'trad': trad, 'comments': comments,
                                                'user_status': user_status, 'receivers': trad.receiver.all(),
                                                'new_num': new_num, 'taken_num': taken_num, 'check_num': check_num,
                                                'oncheck_num': oncheck_num})
    else:
        raise Http404


def edit_trad(request, trad_id):
    trad = Trad.objects.get(id=trad_id)
    if trad.status != 'deleted':
        if trad.author.id == request.user.id:
            if request.method == 'POST':
                form = TradForm(request.POST)
                if form.is_valid():
                    cd = form.cleaned_data
                    trad = Trad(pk=trad_id) # Поменять date - now(), expiration - забивается
                    trad.save_edited(cd, request.user)
                    return HttpResponseRedirect("/" + str(trad.id))
            else:
                form = TradForm(
                    initial={'label': trad.label, 'text': trad.text, 'expiration': trad.expiration}
                )
                form.fields['receiver'].queryset = User.objects.exclude(
                    id=request.user.id) # Нормальный ход (все польщователи кроме меня)
                if trad.receiver:
                    is_common = False
                    receivers = trad.receiver.all()
                    form.fields['receiver'].initial = receivers
                else:
                    is_common = True
            comments = Comment.objects.filter(trad=trad).order_by('date')
            if trad.expiration:
                expiration_time = str(trad.expiration.time().hour) + ":" + str(trad.expiration.time().minute)
                expiration_date = trad.expiration.date().isoformat()
            else:
                expiration_date = None
                expiration_time = None
            new_num, taken_num, check_num, oncheck_num = count_issues(request)
            # Разобраться, почему не возвращает count_values(request)
            return render_to_response('edit_issue.html', {'form': form, 'receivers': receivers, 'user': request.user,
                                                         'is_common': is_common, 'expiration_date': expiration_date,
                                                         'expiration_time': expiration_time, 'comments': comments,
                                                         'new_num': new_num, 'taken_num': taken_num,
                                                         'check_num': check_num, 'oncheck_num': oncheck_num,
                                                         'trad_id': trad.id, 'tomorrow': get_tomorrow()})
        else:
            return HttpResponseRedirect("/")
    else:
        raise Http404


def remove_trad(request, trad_id):
    trad = Trad.objects.get(id=trad_id)
    trad.status = 'deleted'
    trad.save()
    return HttpResponseRedirect("/")


def register(request, hashlink=None):
    check_link = InviteLink.objects.get(link=hashlink)
    if check_link.valid_status == 'valid':
        if request.method == 'POST':
            # Наверное нужно сделать нечто вроде
            # unicoded request.POST['username'] = unicode(request.POST['username'])
            form = UserCreationForm(request.POST)
            if form.is_valid():
                form.save()
                check_link.valid_status = 'burned'
                check_link.save()
                return HttpResponseRedirect("/")
        else:
            form = UserCreationForm()

        return render_to_response("registration/register.html", {
            'form': form, 'hash': hash
        })
    else:
        raise Http404


def generate_link(request):
    if request.is_ajax():
        if request.user.is_superuser == 1:
            try:
                link = InviteLink.objects.create()
                link.generate() # Метод создает хеш md5, делает запись в таблицу
                path = request.build_absolute_uri('../register/') + link.link
                welcome = "<div class='modal-header'> <h2>" + _("Invite ") + "№ " + str(
                    link.id) + " </h2> </div>  <br> <h3>" + _(
                    "Registration link (can be used only once):") + "</h3> <br>  <code>" + path + "</code>"
                return HttpResponse(welcome)
            except:
                return HttpResponse(_('Error occurred'))
        else:
            return HttpResponse(_('You are not administrator'))


# Не имеет смысла выносить формы в отдельный файл
class TradForm(forms.Form):
    label = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-issue-label'}))
    text = forms.CharField(required=False, widget=MarkItUpWidget())
    receiver = forms.ModelMultipleChoiceField(required=False, queryset=User.objects.all(),
                                              widget=forms.SelectMultiple(attrs={'class': 'form-receivers'}))
    expdate = forms.DateField(required=False)
    exptime = forms.TimeField(required=False)
    timezone_offset = forms.CharField(required=False) # Либо смещение локального времени сессии, либо utc


class CommentForm(forms.Form):
    text = forms.CharField(required=False, min_length=1,
                           widget=MarkItUpWidget(attrs={'style': 'width: 99%; height:105px;'}))