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
just like in django's contenttype table. When a model is monitored,
the history of its objects can be queried in django::

    from lizard_history.utils import get_simple_history
    get_simple_history(my_object) # Get basic created / modified info

    from lizard_history.utils import get_history
    get_history(obj=my_object)  # Gets a detailed history list,
                                # including log_entry_id
    get_history(log_entry_id)   # Gets detailed history for one change event.

It is possible to log changes to monitored models even outside a request,
for example when executing management commands. A special fake request
can be started::
    
    from lizard_history.utils import start_fake_request, end_fake_request
    start_fake_request(user=some_user)  # Kwargs will become request attributes
    # Do stuff that should be logged by lizard_history
    end_fake_request()

If the code above is run during a real request, the real request takes
precedence over the fake request.
