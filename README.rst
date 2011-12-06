lizard-history
==========================================

Records full history of django models and mongoengine documents. Only
records if the changes can be related to a request. Only records if the
model or document is present as a MonitoredModel. Changes are recorded
into django's own LogEntry (lizard_admin_history)

The signature of MonitoredModel is the same as that of django's
ContentType. Therefore, to insert all models for your app, you can do
this in the dbshell::

    insert into lizard_history_monitoredmodel
        select * from django_content_type where
        app_label='your_app_label';

When adding manually, note that the model name should be lowercase,
just like in django's contenttype table.
