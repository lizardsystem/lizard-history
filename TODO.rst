TODO
====

- Create a mixin in models that provides some autofields and an optional log message.
- Create a model that contains the whole history table
- Create a migration for it
- Create a signal receiver that records changes for any table on the server
- Have the signal receiver record fields from the mixin and the app.model and the id.
