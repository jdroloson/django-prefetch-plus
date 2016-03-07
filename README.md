=====
Prefetch Plus
=====

Prefetch Plus aims to add additional flexibility to django's built in
prefetch_related functionality. 

Using the built in prefetch_related you can only select objects related through
reverse ForeignKey relationships. With PrefetchPlus you can slect objects related
through any mapping of columns from one table to another.

This allows forsomething much more similar to the capabilities of a
databases left outer join.

Installation
-----------
pip install django-prefetch-plus

Usage
-----------

As Manager:

Prefetch Plus comes with the PrefetchPlusQuerySet which provides a similar
interface to prefetch_related:
```
from prefetch_plus import PrefetchPlusQuerySet
from django.db import models

GENRES = (
    ...
    ('romance', 'Romance'),
    ('mystery', 'Mystery'),
)


class Author(models.Model)
    ...
    genre = models.CharField(
        choices = GENRES
    )
    ...
    objects = PrefetchPlusQuerySet.as_manager()
    
class Book(models.Model)
    ...
    author = models.ForeignKey(
        Author
    )

    genre = models.CharField(
        choices = GENRES
    )
    ...

# We want to have author's of books review other books in the same genre.

# The old way
for author in Author.objects.all():
    # Typical N+1 db query that cannot be resolved with builtin prefetch_related
    author.books_to_review = list(Book.objects.filter(genre=author.genre))
    
# The new way
# This will grab all of the Books that share a genre with any author,
# then it will attach attach the list of books in each genre to the matching
# author(s)
authors = Author.objects.prefetch_plus(
    to_attr='books_to_review',
    query_set=Book.objects.all(),
    obj_cols='genre',
    qset_cols='genre'
).all()
# obj_cols & qset_cols can also be tuples of columns to allow for
# "composite keys". The tuple must be the same length and the matches are
# getattr(object, obj_cols[i]) == getattr(qset_object, qset_cols[i]) for any i
 
# Prefetch plus works across related objects. I highly recommend you remember to
# select_related if you do this. Otherwise, you aren't getting any benefit out
# of this
authors = Author.objects.prefetch_plus(
    to_attr='books_to_review',
    query_set=Book.objects.select_related('author').all(),
    obj_cols='genre',
    qset_cols='author__genre'
).all()
```

Without the manager:

You don't have to use the manager if you don't want, it simply calls the
following helper function at the appropriate time

```
from prefetch_plus import do_prefetch_plus
from django.db import models

GENRES = (
    ...
    ('romance', 'Romance'),
    ('mystery', 'Mystery'),
)


class Author(models.Model)
    ...
    genre = models.CharField(
        choices = GENRES
    )
    ...

class Book(models.Model)
    ...
    author = models.ForeignKey(
        Author
    )

    genre = models.CharField(
        choices = GENRES
    )
    ...

# We want to have author's of books review other books in the same genre.

authors = Author.objects.all()

do_prefetch_plus(
    objects=authors,
    to_attr='books_to_review',
    query_set=Book.objects.all(),
    obj_cols='genre',
    qset_cols='genre'
)
```

