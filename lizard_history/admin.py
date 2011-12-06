from django.contrib.gis import admin

from lizard_history.models import MonitoredModel

class MonitoredModelAdmin(admin.ModelAdmin):
        list_display = ('name', 'app_label', 'model')

admin.site.register(MonitoredModel, MonitoredModelAdmin)
