from django.forms import ModelForm
from django import forms
from grades.models import Activity
from coredata.models import Person
from groups.models import Group

class GroupNameForm(ModelForm):
    class Meta:
        model = Group
        fields = ['name']
    
    def clean_name(self):
        # can't have another group in the course with the same name
        name = self.cleaned_data['name']
        others = Group.objects.filter(courseoffering=self.instance.courseoffering, name=name) \
                .exclude(id=self.instance.id)
        if others:
            raise forms.ValidationError("There is already another group with that name.")

        return name




class ActivityForm(forms.Form):
    selected = forms.BooleanField(label='Selected Activity:', required=False, initial=True)
    
    def __init__(self, *args, **kwargs):
        super(ActivityForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.id:
            self.fields.widget.attrs['readonly'] = True

        
class StudentForm(forms.Form):
    selected = forms.BooleanField(label = 'Selected Student:', required = False)
    
class GroupForSemesterForm(forms.Form):
    selected = forms.BooleanField(label = 'This group is for whole semester', required = False, initial = True)


    

    
