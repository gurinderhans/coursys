import copy
from django.db import models
from grades.models import NumericActivity, NumericGrade, LetterGrade 
from submission.models import SubmissionComponent
from coredata.models import Semester
from groups.models import Group, GroupMember
from datetime import datetime

class ActivityComponent(models.Model):
    """    
    Markable Component of a numeric activity   
    """
    numeric_activity = models.ForeignKey(NumericActivity, null = False)
    max_mark = models.DecimalField(max_digits=5, decimal_places=2, null = False)
    title = models.CharField(max_length=30, null = False)
    description = models.TextField(max_length = 200, null = True, blank = True)
    position = models.IntegerField(null = True, default = 0, blank =True)    
    # set this flag if it is deleted by the user
    deleted = models.BooleanField(null = False, db_index = True, default = False)
    def __unicode__(self):        
        return self.title
    class Meta:
        verbose_name_plural = "Activity Marking Components"
        ordering = ['numeric_activity', 'deleted', 'position']
         
class CommonProblem(models.Model):
    """
    Common problem of a activity component. One activity component can have several common problems.
    """
    activity_component = models.ForeignKey(ActivityComponent, null = False)
    title = models.CharField(max_length=30, null = False)
    penalty = models.IntegerField(null = True, blank = True)
    description = models.TextField(max_length = 200, null = True, blank = True)
    deleted = models.BooleanField(null = False, db_index = True, default = False)
    def __unicode__(self):
        return "common problem %s for %s" % (self.title, self.activity_component)
     
# a callback to avoid path in the filename(that we have append folder structure to) be striped 
def attachment_upload_to(instance, filename):
        """
        append activity_slug/group_slug/ or
               activity_slug/student_userid/ as the parent folder path   
        filename is already in the form of activity_slug/group_slug/orignial_filename or
                                           activity_slug/student_userid/orignial_filename
        """
        marking_files_root = 'marking/files/'
        now = datetime.now()
        time_path = '/'.join([str(now.year), str(now.month), str(now.day)])
        return marking_files_root + time_path + filename
         
class ActivityMark(models.Model):
    """
    General Marking class for one numeric activity 
    """    
      
    overall_comment = models.TextField(null = True, max_length = 1000, blank = True)
    late_penalty = models.IntegerField(null = True, default = 0, blank = True)
    mark_adjustment = models.IntegerField(null = True, default = 0, blank = True)
    mark_adjustment_reason = models.TextField(null = True, max_length = 1000, blank = True)
    file_attachment = models.FileField(null = True, upload_to = attachment_upload_to, blank=True)#TODO: need to add student name or group name to the path  
    
    created_by = models.CharField(max_length=8, null=False, help_text='Userid who gives the mark')
    created_at = models.DateTimeField(auto_now_add=True)
    # For the purpose of keeping a history,
    # need the copy of the mark here in case that 
    # the 'value' field in the related numeric grades gets overridden
    mark = models.DecimalField(max_digits=5, decimal_places=2)     
    
    def __unicode__(self):
        return "Supper object containing additional info for marking"
    class Meta:
        ordering = ['created_at']
    
    def copyFrom(self, obj):
        """
        Copy information form another ActivityMark object
        """
        self.late_penalty = obj.late_penalty
        self.overall_comment = obj.overall_comment
        self.mark_adjustment = obj.mark_adjustment
        self.mark_adjustment_reason = obj.mark_adjustment_reason
        self.file_attachment = obj.file_attachment
    
    def setMark(self, grade):
        self.mark = grade
  

class StudentActivityMark(ActivityMark):
    """
    Marking of one student on one numeric activity 
    """        
    numeric_grade = models.ForeignKey(NumericGrade, null = False)
       
    def __unicode__(self):
        # get the student and the activity
        student = self.numeric_grade.member.person
        activity = self.numeric_grade.activity      
        return "Marking for student [%s] for activity [%s]" %(student, activity)   
      
    def setMark(self, grade):
        """         
        Set the mark
        """
        super(StudentActivityMark, self).setMark(grade)       
        # append folder structure to the file name
        if self.file_attachment:                
            activity = self.numeric_grade.activity
            course = activity.offering
            student = self.numeric_grade.member.person           
            self.file_attachment.name = '/' + course.slug + \
                                        '/' + activity.slug + \
                                        '/' + student.userid + \
                                        '/' + self.file_attachment.name
        
        self.numeric_grade.value = grade
        self.numeric_grade.flag = 'GRAD'
        self.numeric_grade.save()            
        
        
class GroupActivityMark(ActivityMark):
    """
    Marking of one group on one numeric activity
    """
    group = models.ForeignKey(Group, null = False) 
    numeric_activity = models.ForeignKey(NumericActivity, null = False)
         
    def __unicode__(self):
        return "Marking for group [%s] for activity [%s]" %(self.group, self.numeric_activity)
    
    def setMark(self, grade):
        """         
        Set the mark of the group members
        """
        super(GroupActivityMark, self).setMark(grade)    
        # append folder structure to the file name
        if self.file_attachment: 
            course = self.numeric_activity.offering              
            self.file_attachment.name = '/' + course.slug + \
                                        '/' + self.numeric_activity.slug + \
                                        '/' + self.group.slug + \
                                        '/' + self.file_attachment.name
        #assign mark for each member in the group
        group_members = GroupMember.objects.filter(group = self.group, activity = self.numeric_activity, confirmed = True)
        for g_member in group_members:
            try:            
                ngrade = NumericGrade.objects.get(activity = self.numeric_activity, member = g_member.student)
            except NumericGrade.DoesNotExist: 
                ngrade = NumericGrade(activity = self.numeric_activity, member = g_member.student)
            ngrade.value = grade
            ngrade.flag = 'GRAD'
            ngrade.save()            
            
 
class ActivityComponentMark(models.Model):
    """
    Marking of one particular component of an activity for one student  
    Stores the mark the student gets for the component
    """
    activity_mark = models.ForeignKey(ActivityMark, null = False)    
    activity_component = models.ForeignKey(ActivityComponent, null = False)
    value = models.DecimalField(max_digits=5, decimal_places=2)
    comment = models.TextField(null = True, max_length=1000, blank=True)
    
    def __unicode__(self):
        # get the student and the activity
        return "Marking for [%s]" %(self.activity_component,)
        
    class Meta:
        unique_together = (('activity_mark', 'activity_component'),)
        
def get_activity_mark_by_id(activity, student_membership, activity_mark_id): 
     """
     Find the activity_mark with that id if it exists for the student on the activity
     it could be in the StudentActivityMark or GroupActivityMark
     return None if not found.
     """   
    # try StudentActivityMark first 
     try:
         act_mark = StudentActivityMark.objects.select_related().get(id = activity_mark_id)
     except StudentActivityMark.DoesNotExist:
         pass
     else:
         # check consistency with against activity and membership
         # prevent an id query by malicious users 
         num_grade = act_mark.numeric_grade 
         if num_grade.activity == activity and num_grade.member == student_membership:
            return act_mark
        
     # not found, then try GroupActivityMark          
     try:
         act_mark = GroupActivityMark.objects.select_related().get(id = activity_mark_id)
     except GroupActivityMark.DoesNotExist:
         pass
     else:                
         # check the activity_mark consistent with the activity and membership
         # prevent an id query by malicious users 
         if act_mark.numeric_activity == activity:
             group = act_mark.group
             try:
                 group_mem = GroupMember.objects.get(group = group, activity = activity, student = student_membership)
             except GroupMember.DoesNotExist:
                 pass
             else:
                 if group_mem.confirmed == True:
                    return act_mark         
     
     return None

def get_activity_mark_for_group(activity, group, include_all = False):
    
    current_mark = None
    all_marks = GroupActivityMark.objects.filter(group = group, numeric_activity = activity)    
    
    if all_marks.count() != 0 : 
        current_mark = all_marks.latest('created_at')
   
    if not include_all:
        return current_mark
    else:
        return {'current_mark': current_mark, 'all_marks': all_marks}


def get_activity_mark_for_student(activity, student_membership, include_all = False):
     """
     Return the mark for the student on the activity.     
     if include_all is False, only return the current mark which was most lately created 
     and thus is currently valid. Otherwise not only return the current mark but also 
     all the history marks for the student on the activity        
     """  
     current_mark = None
     std_marks = None
     grp_marks = None     
     
     # the mark maybe assigned directly to this student 
     num_grade = NumericGrade.objects.get(activity = activity, member = student_membership)
     std_marks = StudentActivityMark.objects.filter(numeric_grade = num_grade)     
     if std_marks.count() != 0 :
        #get the latest one
        current_mark = std_marks.latest('created_at')
        
     # the mark maybe assigned to this student via the group this student participates for this activity       
     group_mems = GroupMember.objects.select_related().filter(student = student_membership, activity = activity, confirmed = True)
     
     if group_mems.count() > 0:
        group = group_mems[0].group # there should be only one group this student is in
        grp_mark_info = get_activity_mark_for_group(activity, group, True)        
        latest_grp_mark = grp_mark_info['current_mark']
        grp_marks = grp_mark_info['all_marks']
        
        if (current_mark  == None) or \
           (latest_grp_mark != None and latest_grp_mark.created_at > current_mark.created_at):
            current_mark = latest_grp_mark
        
     if not include_all:
         return current_mark
     else:
        return {'current_mark' : current_mark, 
                'marks_individual' : std_marks,
                'marks_via_group' : grp_marks}

def copyCourseSetup(course_copy_from, course_copy_to):
    # copy course setup from one to another
    # TODO: code for copying other kinds of activity can be added on demand
    for numeric_activity in NumericActivity.objects.filter(offering = course_copy_from):
        new_numeric_activity = copy.deepcopy(numeric_activity)
        new_numeric_activity.id = None
        new_numeric_activity.pk = None
        new_numeric_activity.offering = course_copy_to
        week, wkday = course_copy_from.semester.week_weekday(numeric_activity.due_date)
        new_due_date = course_copy_to.semester.duedate(week, wkday, numeric_activity.due_date)
        new_numeric_activity.due_date = new_due_date
        new_numeric_activity.save()
        print "Activity %s is copied" % new_numeric_activity
        for activity_component in ActivityComponent.objects.filter(numeric_activity = numeric_activity):
            new_activity_component = copy.deepcopy(activity_component)
            new_activity_component.id = None
            new_activity_component.pk = None
            new_activity_component.numeric_activity = new_numeric_activity
            new_activity_component.save()
            print "component %s is copied" % new_activity_component
        for submission_component in SubmissionComponent.objects.filter(activity = numeric_activity):
            new_submission_component = copy.deepcopy(submission_component)
            new_submission_component.id = None
            new_submission_component.pk = None
            new_submission_component.activity = new_numeric_activity
            new_submission_component.save()
            print "component %s is copied" % new_submission_component
    
    
