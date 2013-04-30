#author: v.bazhin
#coding: utf-8

from django.db.models import Manager
from django.db.models import Q

class FilterManager(Manager):

    def _unpack_terms(self, filter_dict):
        return reduce(lambda x, y: x | y,
                      [(Q(**terms_set['filter']) & ~Q(**terms_set['exclude']))
                       for terms_set in filter_dict])

    # Фильтруем объекты, исходя из значений словаря
    def filter_set(self, filter_dict):
        for terms_set in filter_dict:
            if 'filter' not in terms_set:
                terms_set['filter'] = {'id':True}
#            if 'exclude' not in terms_set:
                # Добаляем обязательные исключения в список условия
                # Исключаем все удаленные
            if 'exclude' not in terms_set:
                terms_set['exclude'] = {'status': 'deleted'}
            elif 'status' in terms_set['exclude']:
                terms_set['exclude'] += {'status__in': [terms_set['exclude']['status'], 'deleted']}
                del(terms_set['exclude']['status'])
            elif 'status__in' in terms_set['exclude']:
                terms_set['exclude']['status__in'].append('deleted')
        return super(FilterManager, self).get_query_set().filter(self._unpack_terms(filter_dict)).distinct()