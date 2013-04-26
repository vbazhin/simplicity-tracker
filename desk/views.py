#author: v.bazhin
#coding: utf-8

import datetime
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext as _
from desk.models import Issue, Comment, InviteLink
from django.db.models import Q
from forms import IssueForm, CommentForm
# Импортируем фильтр наборов условий
import terms_sets_filter

# Вспомогательные функции (не возвращают HttpResponse, но участвуют в сборке view)
def all(request):
    all_except_me = User.objects.exclude(id=request.user.id)
    return all_except_me

def count_issues(request): # Считаем задания с разными статусами
    iss_num = lambda x: Issue.objects.filter(receiver=request.user, status=x).count() + \
                        Issue.objects.filter(receiver=None, status=x).\
                            exclude(author=request.user).count()
    # Те задания, которые направлены мне, либо общие, исключая те, автор которых - я
    for_check = Issue.objects.filter(author=request.user, status='done').count()
    # Задания направленные мне на проверку
    return iss_num('new'), iss_num('taken'), for_check, iss_num('done')

def get_tomorrow():
    today_dt = datetime.date.today()
    tomorrow_dt = today_dt + datetime.timedelta(days=1)
    tomorrow = tomorrow_dt.isoformat()
    return tomorrow

# Далее идут вьюшки
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect("/")

def login(request):
    auth.login(request)
    # Перенаправление на страницу.
    return HttpResponseRedirect("/")

def comments_gettext_loop(comments):
    for comment in comments:
        if comment.is_status_comment == True:
            comment.get_text()
    return comments

def filter_issues(fltr, request_user):
    # Выбираем из фильтра наборов условий нужный нам словарь
    filter_terms_sets = terms_sets_filter.get_terms_set('issue',request_user)
    if fltr in filter_terms_sets:
        # Выбираем issues соответствующие нашим условиям
        issues = Issue.objects.filter_set(filter_terms_sets[fltr])
    else:
        issues = Issue.objects.filter(Q(receiver=request_user, status=fltr) | \
                                     Q(receiver=None, status=fltr))
    issues = sorted(issues, key=lambda issue: issue.given)
    for issue in issues:
        issue.count_comments()
        issue.define_condition()
    return issues

@login_required
def index(request, fltr='all', add_task=None): # Фильтруем по статусу
    new_num, taken_num, check_num, oncheck_num = count_issues(request)
    # Добавляем задание
    issues = filter_issues(fltr, request.user)
    if request.method == 'POST': # Если сабмичена форма добавления сообщений
        form = IssueForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            issue = Issue()
            issue.add(cd, request.user)
            return HttpResponseRedirect("/")
    else:
        form = IssueForm()
        form.fields['receiver'].queryset = User.objects.exclude(
            id=request.user.id) # Нормальный ход (все польщователи кроме меня)
    return render_to_response('index.html',
                              {'issues': issues,
                               'form': form,
                               'user': request.user,
                               'tomorrow': get_tomorrow(),
                               'new_num': new_num,
                               'taken_num': taken_num,
                               'check_num': check_num,
                               'oncheck_num': oncheck_num,
                               'page_type': 'index',
                               'add_task': add_task}
    )



@login_required
def show_issue(request, related_issue, user_status='group_task_receiver'):
    # Делаю filter, чтобы можно было сразу исключить задания со статусом deleted
    # и не пистаь дополнительное условие if
    issue = Issue.objects.filter(pk=related_issue).exclude(status = 'deleted')[0]
        # escape - html символы
    if request.method == 'POST' and 'comment' in request.POST:
        form = CommentForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            comment = Comment()
            user = User.objects.get(id = 1)
            comment.add(cd, request.user, issue.id)
        return HttpResponseRedirect("")
    elif request.method == 'POST' and 'comment' not in request.POST:
        status = [key for key in request.POST]
        issue.renew_status(status[0], request.user)
        return HttpResponseRedirect("")
    else:
        issue.count_comments()
        issue.define_condition()
        new_num, taken_num, check_num, oncheck_num = count_issues(request)
        comments = comments_gettext_loop(Comment.objects.filter(issue=issue).order_by('date'))
        if request.user in issue.receiver.all():
            user_status = 'receiver'
        if request.user == issue.author:
            user_status = 'author'
        form = CommentForm()
    return render_to_response('issue_page.html', {'form': form,
                                                  'user': request.user,
                                                  'issue': issue,
                                                  'comments': comments,
                                                  'user_status': user_status,
                                                  'receivers': issue.receiver.all(),
                                                  'new_num': new_num,
                                                  'taken_num': taken_num,
                                                  'check_num': check_num,
                                                  'oncheck_num': oncheck_num})

def edit_issue(request, issue_id):
    if request.method == 'POST':
        form = IssueForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            issue = Issue(pk=issue_id)
            issue.save_edited(cd, request.user)
            return HttpResponseRedirect("/" + str(issue.id))
    else:
        issue = Issue.objects.filter(id=issue_id,
                                   author=request.user).exclude(status='deleted')[0]
        form = IssueForm(
            initial={'label': issue.label,
                     'text': issue.text,
                     'expiration': issue.expiration}
        )
        form.fields['receiver'].queryset = User.objects.exclude(id=request.user.id)
        if issue.receiver:
            is_common = False
            receivers = issue.receiver.all()
            form.fields['receiver'].initial = receivers
        else:
            is_common = True
        comments = comments_gettext_loop(Comment.objects.filter(issue=issue).order_by('date'))
        if issue.expiration:
            # Тут надо что-то делать
            expiration_time = str(issue.expiration.time().hour) + ":" + \
                              str(issue.expiration.time().minute)
            expiration_date = issue.expiration.date().isoformat()
        else:
            expiration_date = expiration_time = None
        new_num, taken_num, check_num, oncheck_num = count_issues(request)
        # Разобраться, почему не возвращает count_values(request)
        return render_to_response('edit_issue.html', {'form': form,
                                                      'receivers': receivers,
                                                      'user': request.user,
                                                     'is_common': is_common,
                                                     'expiration_date': expiration_date,
                                                     'expiration_time': expiration_time,
                                                     'comments': comments,
                                                     'new_num': new_num,
                                                     'taken_num': taken_num,
                                                     'check_num': check_num,
                                                     'oncheck_num': oncheck_num,
                                                     'issue_id': issue.id,
                                                     'tomorrow': get_tomorrow()})


def remove_issue(request, issue_id):
    issue = Issue.objects.get(id=issue_id)
    if issue.author == request.user:
        issue.status = 'deleted'
        issue.save()
    return HttpResponseRedirect("/")

def register(request, hashlink=None):
    # Проверяется валидность ссылки и меняется ее статус на burned
    check_link = InviteLink.objects.get(link=hashlink)
    if check_link.valid_status == 'valid' and request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            check_link.valid_status = 'burned'
            check_link.save()
            return HttpResponseRedirect("/")
    if check_link.valid_status == 'valid':
        form = UserCreationForm()
        return render_to_response("registration/register.html", {
            'form': form, 'hash': hash
        })
    else:
        raise Http404

def generate_link(request):
    if request.is_ajax() and request.user.is_superuser == 1:
        link = InviteLink.objects.create()
        # Метод создает хеш md5, делает запись в таблицу
        link.generate()
        path = request.build_absolute_uri('../register/') + link.link
        welcome = "<div class='modal-header'> <h2>" + _("Invite ") + "№ " + \
        str(link.id) + " </h2> </div>  <br> <h3>" + \
              _("Registration link (can be used only once):") + \
                  "</h3> <br>  <code>" + path + "</code>"
        return HttpResponse(welcome)
    else:
        return Http404
