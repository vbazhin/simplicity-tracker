#author: v.bazhin
#coding: utf-8


def get_terms_set(model_name, *args, **kwargs):

    request_user = args[0]

    issue = {
            # Нельзя связанные объекты получать с помощью filter __in,
            # поэтому конструируем запросы отдельно
            'all': [{'filter': {'receiver': request_user},
                     'exclude':{'status__in': ['deleted']},
                     },
                    {'filter': {'receiver': None},
                     'exclude': {'status__in': ['deleted']},
                     },
                    {'filter': {'author': request_user},
                     'exclude': {'status__in': ['deleted']},
                     }],
            'current': [{'filter': {'receiver': request_user,
                                    'status__in': ['new', 'taken', 'done']},
                         },
                        {'filter': {'receiver': None,
                                    'status__in': ['new', 'taken', 'done']},
                         }],
            'check': [{'filter': {'author': request_user,
                                  'status__in': ['done']},
                       }],
            'givenbyme': [{'filter': {'author': request_user},
                           'exclude': {'status__in': ['deleted']},
                           }],
            'error': [{'filter': {'receiver': request_user,
                                  'status__in': ['error']},
                       },
                      {'filter': {'receiver': None,
                                  'status__in': ['error']},
                       },
                      {'filter': {'author': request_user,
                                  'status__in': ['error']},
                       }],
            'new': [{'filter': {'receiver': request_user,
                                'status__in': ['new']},
                     'exclude': {'author': request_user},
                     },
                    {'filter': {'receiver': None,
                                'status__in': ['new']},
                     'exclude': {'author': request_user},
                     }]
        }

    return locals()[model_name]