TODO
====
- make tests

- make it work for annotations / mongostuff too.
  involves changemessage and content_type problem. Maybe insert own contenttypes? Uh, oh.

- check for something set on the meta to start keeping history, or in the settings of the site.

- think about many-to-many...

- solve the pre-/post- problem: using pre-save, we don't know if the
  save was succesful and what the pk became; using post-save, we don't
  know what the original was. So the whole logentry should be kept in some
  local storage again, and a pk and verification added afterwards. Tip
  from reinout, just put it on the request, but what if multiple saves
  are carried out? You can expect them to be in the correct order? Do
  some testing.
  
- prevent django admin to do logentries by itself? Otherwise, you get double entries.
