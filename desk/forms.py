class AddTrad(forms.Form):

    label = forms.CharField(widget=forms.TextInput(attrs={'style':'width:650px;'}))
    text = forms.CharField(required=False, widget=MarkItUpWidget(attrs={'style':'width: 99%; height:105px;'}))
    receiver = forms.ModelMultipleChoiceField(required=False, queryset=User.objects.all(), widget=forms.SelectMultiple(attrs={'style':'width:300px; height:200px;'}))
    expdate = forms.DateField(required=False)
    exptime = forms.TimeField(required=False)
    timezone_offset =forms.CharField(required=False)


class CommentForm(forms.Form):
    text = forms.CharField(required=False, widget=MarkItUpWidget(attrs={'style':'width: 99%; height:105px;'}))