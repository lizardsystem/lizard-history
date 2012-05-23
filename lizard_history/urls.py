# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.conf.urls.defaults import include
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from django.contrib import admin

from lizard_ui.urls import debugmode_urlpatterns
from lizard_history import views

admin.autodiscover()

NAME_PREFIX = 'lizard_history_'

urlpatterns = patterns(
    '',
    (r'^admin/', include(admin.site.urls)),
    url(r'^api_object/(?P<log_entry_id>[0-9]+)/$',
        views.ApiObjectView.as_view(),
        name=NAME_PREFIX + 'api_object'),
    url(r'^other_object/(?P<log_entry_id>[0-9]+)/$',
        views.OtherObjectView.as_view(),
        name=NAME_PREFIX + 'other_object'),
    url(r'^wbconfiguration/area_object_configuration/'
        '(?P<log_entry_id>[0-9]+)/$',
        views.AreaObjectConfigurationView.as_view(),
        name=NAME_PREFIX + 'wbconfiguration_area_object_configuration'),
    url(r'^wbconfiguration/area_configuration/(?P<log_entry_id>[0-9]+)/$',
        views.AreaConfigurationView.as_view(),
        name=NAME_PREFIX + 'wbconfiguration_area_configuration'),
    )
urlpatterns += debugmode_urlpatterns()
