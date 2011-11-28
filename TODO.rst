TODO
====
- make tests

- make it work for annotations / mongostuff too.

- check for something set on the meta to start keeping history, or in the settings of the site.

- think about many-to-many...

- solve the pre-/post- problem: using pre-save, we don't know if the
  save was succesful and what the pk became; using post-save, we don't
  know what the original was. So the whole logentry should be kept in some
  local storage again, and a pk and verification added afterwards.
  
- prevent django admin to do logentries by itself? Otherwise, you get double entries.
