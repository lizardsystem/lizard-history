TODO
====

- make tests that
    save a new model without pk
    save a new model with pk
    change a model
    delete a model
    save a new document without pk
    save a new document with pk
    change a document
    delete a document
    check if logentrie are written for each of the above

- prepare a separate logentry table for mongostuff
- prepare a separate contenttype table for mongostuff

- do something with many to many saves about many-to-many...

- Methods to get the history of any object, with optional depth, if possible via the object, or otherwise via some method from lizard-history

- Have db actions without a request also logged properly. Currently, it's disabled because there is no request and therefore no original can be stored on the request.
