from django.contrib import admin
from core.models import (
	Workspace,
	WorkspaceResource,
	RejectReason,
	Event,
)

# Register your models here.

admin.site.register(Workspace)
admin.site.register(WorkspaceResource)
admin.site.register(RejectReason)
admin.site.register(Event)
