from django.contrib import admin
from .models import LeaveDetails
from .models import LeaveMaster

# Register your models here.
admin.site.register(LeaveDetails),
admin.site.register(LeaveMaster)