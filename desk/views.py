#author: v.bazhin
#coding: utf-8

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from desk.models import Trad, Comment, InviteLink
from django import forms
from markitup.widgets import MarkItUpWidget, MarkupTextarea
import datetime
import json
from django.contrib.auth.models import User
from django.utils.html import escape
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm


# Вспомогательные функции (не возвращают HttpResponse, но участвуют в сборке view)
def all():
    all_except_me = User.objects.exclude(id = request.user.id)
    return all_except_me

def count_issues(request): # Считаем задания с разными статусами
    iss_num = lambda x: Trad.objects.filter(receiver = request.user, status = x).count() + Trad.objects.filter(receiver = None, status = x).exclude(author=request.user).count()
    # Те задания, которые направлены мне, либо общие, исключая те, автор которых - я
    for_check = Trad.objects.filter(author = request.user, status = 'done').count() # Задания направленные мне на проверку
    return iss_num('new'), iss_num('taken'), for_check, iss_num('done')

def get_tomorrow():
    today = datetime.date.today()
    tomorrow = datetime.date(today.year, today.month, today.day + 1).isoformat()
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

@login_required
def index(request, fltr = 'all', add_task = None): # Фильтруем по статусу
    if fltr == 'all':
        trads = list(Trad.objects.filter(receiver = request.user))
        trads += list(Trad.objects.filter(receiver = None).exclude(author = request.user) )
        #trads += list(Trad.objects.filter( Q(receiver = None) & ~Q(author = request.user)))
        trads += list(Trad.objects.filter(author = request.user))
        trads = sorted(trads, key=lambda trad: trad.given)
        #Делаю list, а не queryset т.к. при совместном запрсое разможножает объекты, созданные request.user, упорядочиваю
    elif fltr == 'current':
        trads = Trad.objects.filter(receiver = request.user, status = 'new') | Trad.objects.filter(receiver = request.user, status = 'taken') | Trad.objects.filter(receiver = request.user, status = 'done') | Trad.objects.filter(receiver = None, status = 'new') | Trad.objects.filter(receiver = None, status = 'taken') | Trad.objects.filter(receiver = None, status = 'done')
    elif fltr == 'check':
        trads = Trad.objects.filter(author = request.user, status = 'done') | Trad.objects.filter(author = request.user, status = 'done')
    elif fltr == 'givenbyme':
        trads = Trad.objects.filter(author = request.user)
    else:
        trads = Trad.objects.filter(receiver = request.user, status = fltr) | Trad.objects.filter(receiver = None, status = fltr)
    for trad in trads:
        trad.comments_num = Comment.objects.filter(trad = trad).count() # Cчитаем комментарии
        trad.define_condition()
    new_num, taken_num, check_num, oncheck_num = count_issues(request)
    # Добавляем задание
    if request.method == 'POST': # Если сабмичена форма добавления сообщений
        form = AddTrad(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            tz_offset = cd['timezone_offset']
            expdate = cd['expdate']
            exptime = cd['exptime']
            if expdate == None:
                exp_value = 'No'
                exp = None
            else:
                exp_value = 'Yes'
                exp = datetime.datetime.combine(expdate, exptime) # Соединяем дату и время
            #if exptime == None:
                #is_exp = 'No'
            new_trad = Trad(label = escape(cd['label']), text = escape(cd['text']), given=datetime.datetime.now(), is_expiration = exp_value, expiration=exp, status='new', author = request.user) # Поменять date - now(), expiration - забивается
            new_trad.save()
            receivers = cd['receiver']
            #if not receivers:
                #receivers = User.objects.exclude(id = request.user.id)
            new_trad.receiver = receivers
            return HttpResponseRedirect("/")
    else:
        form = AddTrad()
        form.fields['receiver'].queryset = User.objects.exclude(id = request.user.id) # Нормальный ход (все польщователи кроме меня)
    return render_to_response('index.html', {'trads': trads, 'form': form, 'user' : request.user, 'tomorrow' : get_tomorrow(), 'new_num': new_num, 'taken_num': taken_num, 'check_num': check_num, 'oncheck_num': oncheck_num, 'page_type' : 'index', 'add_task': add_task })


def show_trad(request, related_trad,  user_status = 'group_task_receiver'):
    try:
        trad = Trad.objects.get(pk = related_trad)
        trad.comments_num = Comment.objects.filter(trad = trad).count() # Cчитаем комментарии
        trad.define_condition()
        new_num, taken_num, check_num, oncheck_num = count_issues(request)
        comments = Comment.objects.filter(trad = trad).order_by('date')
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
                    comment = Comment(text = escape(cd['text']), date = datetime.datetime.now(), trad_id = trad.id,  author = request.user)
                    comment.save()
            else:
                trad.renew_status(request.POST, request.user) # Новый статус (объеденить метод с комментированием)
                return HttpResponseRedirect("")
        else:
            form = CommentForm()
        return render_to_response('trad.html', {'form': form, 'user' : request.user, 'trad': trad, 'comments': comments, 'user_status': user_status, 'receivers' : trad.receiver.all(), 'new_num': new_num, 'taken_num': taken_num, 'check_num': check_num, 'oncheck_num': oncheck_num })
    except:
        raise Http404


def edit_trad(request, trad_id):
    try:
        trad = Trad.objects.get(id= trad_id)
        if trad.author.id == request.user.id:
            if request.method == 'POST':
                form = AddTrad(request.POST)
                if form.is_valid():
                    cd = form.cleaned_data
                    expdate = cd['expdate']
                    exptime = cd['exptime']
                    if expdate == None:
                        exp_value = 'No'
                        exp = None
                    else:
                        exp_value = 'Yes'
                        exp = datetime.datetime.combine(expdate, exptime)
                        #if exptime == None:
                        #is_exp = 'No'
                    trad = Trad(pk = trad_id, label = cd['label'], text = cd['text'], given=datetime.datetime.now(),
                    is_expiration = exp_value, expiration=exp, status='new', author = request.user) # Поменять date - now(), expiration - забивается
                    trad.save()
                    receivers = cd['receiver']
                    if not receivers:
                        receivers = User.objects.exclude(id = request.user.id)
                    trad.receiver = receivers
                    comment = Comment(text = u'Задание изменено пользователем ' + request.user.username, date = datetime.datetime.now(), trad_id = trad.id,  author = request.user)
                    comment.save()
                    return HttpResponseRedirect("/" + str(trad.id))
            else:
                form = AddTrad(
                    initial={'label':trad.label , 'text':trad.text, 'expiration':trad.expiration}
                )
                form.fields['receiver'].queryset = User.objects.exclude(id = request.user.id) # Нормальный ход (все польщователи кроме меня)

            comments = Comment.objects.filter(trad = trad).order_by('date')

            if trad.expiration:
                expiration_time = str(trad.expiration.time().hour) + ":" + str(trad.expiration.time().minute)
                expiration_date = trad.expiration.date().isoformat()
            else:
                expiration_date = None
                expiration_time = None
            new_num, taken_num, check_num, oncheck_num = count_issues(request)
            # Разобраться, почему не возвращает count_values(request)
            return render_to_response('edit_trad.html', { 'form': form, 'user' : request.user, 'expiration_date' : expiration_date , 'expiration_time' : expiration_time, 'comments' : comments, 'new_num': new_num, 'taken_num': taken_num, 'check_num': check_num, 'oncheck_num': oncheck_num, 'trad_id': trad.id, 'tomorrow': get_tomorrow() })
        else:
            return HttpResponseRedirect("/")
    except:
        raise Http404

def register(request, hashlink=None):
    try:
        check_link = InviteLink.objects.get(link = hashlink)
        if check_link.valid_status == 'valid':
            if request.method == 'POST':
                # Наверное нужно сделать нечто вроде
                # unicoded request.POST['username'] = unicode(request.POST['username'])
                form = UserCreationForm(request.POST)
                if form.is_valid():
                    form.save()
                    check_link.valid_status = 'burned'
                    check_link.save()
                    if request.user.is_authenticated():
                        auth.logout(request)
                    return HttpResponseRedirect("/")
            else:
                form = UserCreationForm()

            return render_to_response("registration/register.html", {
                'form': form, 'hash': hash
            })
        else:
            raise Http404
    except:
        raise Http404


def generate_link(request):
    if request.is_ajax():
        if request.user.is_superuser == 1:
            try:
                link = InviteLink.objects.create()
                link.generate() # Метод создает хеш md5, делает запись в таблицу
                path = request.build_absolute_uri('../register/') + link.link
                welcome = '<div class="modal-header"> <h2> Приглашение №' + str(link.id) + "</h2> </div>  <br> <h3> Ссылка на регистрацию (действует 1 раз): </h3> <br>  <code>" + path + "</code>"
                return  HttpResponse(welcome)
            except:
                return HttpResponse('Произошла ошибка')
        else:
            return HttpResponse("Вы не администратор, а только притворяетесь")




# Не имеет смысла выносить формы в отдельный файл
class AddTrad(forms.Form):

    label = forms.CharField(widget=forms.TextInput(attrs={'style':'width:597px;'}))
    text = forms.CharField(required=False, widget=MarkItUpWidget(attrs={'style':'width: 99%; height:105px;'}))
    receiver = forms.ModelMultipleChoiceField(required=False, queryset=User.objects.all(), widget=forms.SelectMultiple(attrs={'style':'width:300px; height:200px;'}))
    expdate = forms.DateField(required=False)
    exptime = forms.TimeField(required=False)
    timezone_offset =forms.CharField(required=False) # Либо смещение локального времени сессии, либо utc


class CommentForm(forms.Form):
    text = forms.CharField(required=False, widget=MarkItUpWidget(attrs={'style':'width: 99%; height:105px;'}))