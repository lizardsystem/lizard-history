Changelog of lizard-history
===================================================


0.2.10 (2012-06-26)
-------------------

- Improve change_message, use __dict__ now instead of django serializer.


0.2.9 (2012-06-18)
------------------

- Remove dependencies on lizard-esf and lizard-wbconfiguration.
- Move specific wbconfiguration method to lizard-wbconfiguration.


0.2.8 (2012-05-31)
------------------

- Fix bug when objects are pre_saved, but not actually saved,
  for example due to database errors.


0.2.7 (2012-05-29)
------------------

- Implement special case of esf tree.

- Tweak history for use with wbconfiguration.


0.2.6 (2012-05-10)
------------------

- Show full name or username if no full name in get_simple_history
- Remove converting to str result for get_simple_history


0.2.5 (2012-05-10)
------------------

- Add specific signal and middleware for history.
- Rework the handlers to get simpler code.
- Add view for object_api's for use in vss.
- Remove old mongo code.
- Implement deletion logging.
- Add templatetag for formatting logged datetimes.


0.2.4 (2012-04-13)
------------------

- Add cleaning to pre_save handler to fix serialization of unsaved objects.


0.2.3 (2012-02-17)
------------------

- Remove get_full_history method

- Add get_history method that can return full history or single logentry


0.2.2 (2012-02-13)
------------------

- Add handling of optional 'lizard_history_summary' attribute on saved object.


0.2.1 (2012-01-23)
------------------

- Removes use of dictionary comprehension (Python 2.7 and higher)


0.2 (2012-01-20)
----------------

- Adds method get_simple_history to retrieve history for objects from LogEntry

- Adds method get_full_history to retrieve history for objects from LogEntry

- Changes change_text to parseable json for django models


0.1.1 (2011-12-07)
------------------

- Excludes all models that are involved in syncdb, migrate.


0.1 (2011-12-06)
----------------

- Initial library skeleton created by nensskel.  [Arjan Verkerk]

- Adds django-tls to be able to use the request for logging user

- Adds receivers that log changes to django models in django admin's logentry

- Adds configchecker to check for correct middleware in site

- Adds a database model and migration to keep track of models that should be monitored

- Adds tools to hash and diff models

