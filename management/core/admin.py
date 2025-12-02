from django.contrib import admin
from core.models import (
	Workspace,
	WorkspaceResource,
	RejectReason,
	Event, 
	EventDetail,
	EventSpace
)

# Register your models here.

admin.site.register(Workspace)
admin.site.register(WorkspaceResource)
admin.site.register(RejectReason)
admin.site.register(Event)
admin.site.register(EventDetail)
admin.site.register(EventSpace)
