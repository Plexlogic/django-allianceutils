# Alliance Utils

A collection of utilities for django projects.

* [Installation](#installation)
* [Usage](#usage)
    * [API](#api)
    * [Auth](#auth)
    * [Commands](#commands)
    * [Decorators](#decorators)
    * [Filters](#filters)
    * [Management](#management)
        * [Checks](#checks)
    * [Middleware](#middleware)
    * [Migrations](#migrations)
    * [Models](#models)
    * [Serializers](#serializers)
    * [Storage](#storage)
    * [Template Tags](#template-tags)
    * [Util](#util)
    * [Views](#views)
    * [Webpack](#webpack)
* [Changelog](#changelog)

## Installation

`pip install -e git+git@gitlab.internal.alliancesoftware.com.au:alliance/alliance-django-utils.git@master#egg=allianceutils`

## Usage

### API

#### CacheObjectMixin

**Status: No unit tests**

Caches the result of `get_object()` in the request
* TODO: Why cache this on `request` and not on `self`?
    * If you are customising `get_object()`, `django.utils.functional.cached_property` is probably simpler 

```python
class MyViewSet(allianceutils.api.mixins.CacheObjectMixin, GenericViewSet):
    # ...
```  

#### Permissions

##### SimpleDjangoObjectPermissions

**Status: No unit tests**

Permission class for Django Rest Framework that adds support for object level permissions.

Differs from just using DjangoObjectPermissions because it
* does not require a queryset
* uses a single permission for all request methods

Notes
* As per [DRF documentation](http://www.django-rest-framework.org/api-guide/permissions/#object-level-permissions): get_object() is only required if you want to implement object-level permissions
* **WARNING** If you override `get_object()` then you need to *manually* invoke `self.check_object_permissions(self.request, obj)`

Setup
* To apply to all classes in django rest framework:

```python
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        # default to requiring authentication & a role
        # you can override this by setting the permission_classes to AllowAny in the view
        'rest_framework.permissions.IsAuthenticated',
        'allianceutils.api.permissions.SimpleDjangoObjectPermissions',
    ),
}
```

* To apply to one particular view, override `permission_required`
```python
class MyAPIView(PermissionRequiredAPIMixin, APIView):
        permission_required = 'my_module.my_permission'

        # You do not have to override get_object() but if you do you must explicitly call check_object_permissions() 
        def get_object(self):
            obj = get_object_or_404(self.get_queryset())
            self.check_object_permissions(self.request, obj)
            return obj
```

If you have no object level permissions (eg. from rules) then it will just do a static permission check.


##### GenericDjangoViewsetPermissions

**Status: No unit tests**

### Auth

FIXME

### Commands

#### autodumpdata

* Designed to more conveniently allow dumping of data from different models into different fixtures
* Strongly advised to also use the [Serializers](#serializers)
* If `autodumpdata` is invoked without a fixture name, it defaults to `dev`
* For each model, you add a list of fixture names that this model should be part of
    * `fixures_autodump`
        * Fixtures in JSON format
    * `fixtures_autodump_sql`
        * Fixures in SQL
        * Only works with mysql
        * Much likelier to cause merge conflicts and are less readable by developers but are significantly faster.
        * Should only be used for large tables where django's default fixture loading is too slow.
    
* Example
    * The following will dump the Customer model as part of the `customers` and `test` fixtures
    * The following will also dump the Customer model in SQL as part of the `fast` fixture

```python
class Customer(models.Model):
    fixtures_autodump = ['customers', 'test']
    fixtures_autodump_sql = ['fast']
```

* To add autodump metadata to models that are part of core django, add the following code to one of your apps
    * This can be particularly useful for dumping django group permissions (which you typically want to send to a live server) separately from test data

```python
# This will take the default fixture dumping config for this app and add the core auth.group and authtools.user
# tables to the groups and users fixtures respectively 
def get_autodump_labels(app_config, fixture):
    import allianceutils.management.commands.autodumpdata
    extras = {
        'groups': [
            'auth.group',
        ],
        'users': [
            'authtools.user',
        ],
    }
    original_json, original_sql = allianceutils.management.commands.autodumpdata.get_autodump_labels(app_config, fixture)
    for fixture in extras:
        original_json[fixture] = original_json.get(fixture, []) + extras[fixture]
    return (original_json, original_sql)
```

#### mysqlquickdump

* Command to quickly dump a mysql database
    * Significantly faster than django fixtures
* Can be useful for saving & restoring the state of the database in test cases
    * Not intended to be used on production servers
* Expects that DB structure will not change
* See `./manage.py mysqlquickdump --help` for usage details

#### mysqlquickload

* Load a database dumped with `mysqlquickdump`
* See `./manage.py mysqlquickload --help` for usage details

### Decorators

### Filters

#### MultipleFieldCharFilter

Search for a string across multiple fields. Requires `django_filters`.

* Usage 

```python
from allianceutils.filters import MultipleFieldCharFilter

# ...
# In your filter set (see django_filters for documentation)
customer = MultipleFieldCharFilter(names=('customer__first_name', 'customer__last_name'), lookup_expr='icontains')
```

### Management

FIXME

#### Checks

##### check_url_trailing_slash

* Checks that your URLs are consistent with the `settings.APPEND_SLASH` using a [django system check](https://docs.djangoproject.com/en/dev/ref/checks/)
* In your [app config](https://docs.djangoproject.com/en/1.11/ref/applications/#for-application-authors) 

```python
from django.apps import AppConfig
from django.core.checks import register
from django.core.checks import Tags

from allianceutils.checks import check_url_trailing_slash

class MyAppConfig(AppConfig):
    # ...

    def ready(self):
        # trigger checks to register
        check = check_url_trailing_slash(expect_trailing_slash=True)
        register(check=check, tags=Tags.url)
```

* Optional arguments to `check_url_trailing_slash`
    * `ignore_attrs` - skip checks on url patterns where an attribute of the pattern matches something in here (see example above)
        * Most relevant attributes of a `RegexURLResolver`:
            * `_regex` - string used for regex matching. Defaults to `[r'^$']`
            * `app_name` - app name (only works for `include()` patterns). Defaults to `['djdt']` (django debug toolbar)
            * `namespace` - pattern defines a namespace
            * `lookup_str` - string defining view to use. Defaults to `['django.views.static.serve']`
        * Note that if you skip a resolver it will also skip checks on everything inside that resolver  

### Middleware

#### CurrentUserMiddleware

* Middleware to enable accessing the currently logged-in user without a request object.
    * Properly handles multithreaded python by keeping track of the current user in a `dict` of `{'threadId': User}` 

* Setup
    * Add `allianceutils.middleware.CurrentUserMiddleware` to `MIDDLEWARE`.

* Usage

```python
from allianceutils.middleware import CurrentUserMiddleware

user = CurrentUserMiddleware.get_user()
```

#### QueryCountMiddleware

* Warns if query count reaches a given threshold
    * Threshold can be changed by setting `settings.QUERY_COUNT_WARNING_THRESHOLD`

* Usage
    * Add `allianceutils.middleware.CurrentUserMiddleware` to `MIDDLEWARE`.
    * Uses the `warnings` module to raise a warning; by default this is suppressed by django
        * To ensure `QueryCountWarning` is never suppressed  
```python
warnings.simplefilter('always', allianceutils.middleware.QueryCountWarning)
```

* To increase the query count limit for a given request, you can increase `request.QUERY_COUNT_WARNING_THRESHOLD`
    * Rather than hardcode a new limit, you should increment the existing value
    * If `request.QUERY_COUNT_WARNING_THRESHOLD` is falsy then checks are disabled for this request 
```python
def my_view(request, *args, **kwargs):
    request.QUERY_COUNT_WARNING_THRESHOLD += 10
    ...

```
 

### Migrations

FIXME

### Models

#### Utility functions / classes

##### Authentication functions
* `add_group_permissions(group_id, codenames)`
    * Add permissions to a given group (permissions must already exist)
* `get_users_with_permission(permission)`
    * Single-permission shorthand for `get_users_with_permissions` 
* `get_users_with_permissions(permissions)`
    * Gets all users with any of the specified static permissions

##### combine_querysets_as_manager
* Replacement for django_permanent.managers.MultiPassThroughManager which no longer works in django 1.8
* Returns a new Manager instance that passes through calls to multiple underlying queryset_classes via inheritance 

##### NoDeleteModel

* A model that blocks deletes in django
    * Can still be deleted with manual queries
* Read django docs about [manager inheritance](https://docs.djangoproject.com/en/1.11/topics/db/managers/#custom-managers-and-model-inheritance)
    * If you wish add your own manager, you need to combine the querysets:

```python
class MyModel(NoDeleteModel):
        objects = combine_querysets_as_manager(NoDeleteQuerySet, MyQuerySet)
```  

#### GenericUserProfile

Allows you to iterate over a `User` table and have it return the corresponding `UserProfile` records without any extra queries

Example:

```python
# ------------------------------------------------------------------
# base User model 
class UserManager(django.contrib.auth.models.UserManager):
    def get_by_natural_key(self, username):
        return self.get(username=username)


class User(django.contrib.auth.models.AbstractUser):
    objects = UserManager()

    def natural_key(self):
        return (self.username,)


# ------------------------------------------------------------------
# Custom user profiles
class CustomerProfile(User):
    customer_details = models.CharField(max_length=191)


class AdminProfile(User):
    admin_details = models.CharField(max_length=191)


# ------------------------------------------------------------------
# Usually you wish to inherit default UserManager functionality
class GenericUserProfileManager(allianceutils.models.GenericUserProfileManager, User._default_manager.__class__):
    use_proxy_model = False

    @classmethod
    def user_to_profile(cls, user):
        if hasattr(user, 'customerprofile'):
            return user.customerprofile
        elif hasattr(user, 'adminprofile'):
            return user.adminprofile
        return user

    @classmethod
    def select_related_profiles(cls, queryset):
        return queryset.select_related(
            'customerprofile',
            'adminprofile',
        )

class GenericUserProfile(User):
    objects = GenericUserProfileManager()

    class Meta:
        proxy = True

```

* `GenericUserProfileManager` class cannot know when being constructed what `Model` it will be attached to so you must manually define any model manager(s) you wish to inherit from  
* If `use_proxy_model` is `False` then the underlying `User` model will be returned from queries instead of the proxy model
    * `user_to_profile()` can use any logic you wish
    * `select_related_profiles()` should include all relevant profiles
* If `settings.AUTH_USER_MODEL is set to GenericUserProfile` then `AuthenticationMiddleware` will cause `request.user` to contain the appropriate profile with no extra queries  
    * Due to a django limitation, if `AUTH_USER_MODEL` is set then you cannot use `django.contrib.auth.models.User`, you must create your own `User` table (usually based on `AbstractUser`)  

### Serializers

#### JSON Ordered

* A version of django's core json serializer that outputs field in sorted order
* The built-in one uses a standard `dict` with completely unpredictable order which makes fixture diffs often contain field ordering changes

* Setup
    * Add to `SERIALIZATION_MODULES` in your settings
    * This will allow you to do fixture dumps with `--format json_ordered`
    * Note that django treats this as the file extension to use; `autodumpdata` overrides this to `.json`

```python
SERIALIZATION_MODULES = {
    'json_ordered': 'allianceutils.serializers.json_ordered',
}
```

#### JSON ORM Inheritance Fix

* Django does not properly handle (de)serialise models with natural keys where the PK is a FK
    * This shows up particularly with multi-table inheritance and the user profile pattern
    * https://code.djangoproject.com/ticket/24607
        * Patch was accepted into 1.11 but then removed
        * We are willing to deal with potentially spurious migrations in order to have fixtures work
* We need to replace not only the serializer but also the deserializer
* Note that child models will not inherit the parent `Manager` if the parent is not `abstract`; you need to define a `Manager` that has a `get_by_natural_key()` in each descendant model if you use FK references to the descendant model. 

```python
SERIALIZATION_MODULES = {
    'json': 'allianceutils.serializers.json_orminheritancefix',
}
```

### Storage

* Requires `django-storages` and `boto` to be installed

* Use the below if you are using S3 for file storage and want to prefix media and / or static files - otherwise they will all be dumped unprefixed in the bucket.

* Configure S3 for use with S3 Boto

```python
AWS_ACCESS_KEY_ID = 'ACCESS_KEY'
AWS_STORAGE_BUCKET_NAME = 'bucket-name'
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
```

#### StaticStorage

* An extension to S3BotoStorage that specifies a prefix for static files.
* Allows you to put static files and media files in S3 without worrying about clobbering each other.
* Note that if using on Heroku this doesn't play nice with pipelines so you probably don't want to use it
* Configuration

```python
STATICFILES_STORAGE = 'allianceutils.storage.StaticStorage'
STATICFILES_LOCATION="static"

STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, STATICFILES_LOCATION)
```

#### MediaStorage

* An extension to S3BotoStorage that specifies a prefix for static files.
* Allows you to put static files and media files in S3 without worrying about clobbering each other.

Configuration:

```python
DEFAULT_FILE_STORAGE = 'allianceutils.storage.MediaStorage'
MEDIAFILES_LOCATION="media"

MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
```

### Template tags

#### script_json

* Dump a python object into json for embedding in a script tag

* Usage

```html
{% load script_json %}

<script>window.__APP_SETTINGS = {{ APP_SETTINGS|script_json }};</script>
```

#### alliance_bundle

* A wrapper to the webpack_bundle tag that accounts for the fact that
    * in production builds there will be separate JS + CSS files
    * in dev builds the CSS will be embedded in the webpack JS bundle
* Assumes that each JS file is paired with a CSS file.
    * If you are only including JS without extracted CSS then use `webpack_bundle`, or include a placeholder CSS bundle (will just include a webpack stub; if you are using `django-compress` then overhead from this will be minimal)

* Example Usage

```html
{% load alliance_bundle %}
<html>
<head>
  {% alliance_bundle 'shared-bower-jqueryui' 'css' %}
  {% alliance_bundle 'shared-bower-common' 'css' %}
  {% alliance_bundle 'shared-styles' 'css' %}
</head>
<body>
  
  ...
  
  {% alliance_bundle 'shared-bower-jqueryui' 'js' %}
  {% alliance_bundle 'shared-bower-common' 'js' %}
  {% alliance_bundle 'shared-styles' 'js' %}
</body>
</html>
```

* In production (`not settings.DEBUG`), the css tag will be a standard `<link rel="stylesheet" ...>` tag 
* In development (`settings.DEBUG`), the css tag will be a webpack JS inclusion that contains the CSS (and inherit webpack hotloading etc)

### Util

#### python_to_django_date_format

Converts a python [strftime/strptime](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior) datetime format string into a []django template/PHP](https://docs.djangoproject.com/en/dev/ref/templates/builtins/#std:templatefilter-date) date format string

#### retry_fn

* Repeatedly (up to a hard limit) call specified function while it raises specified exception types or until it returns

```python
from allianceutils.util import retry_fn

# Generate next number in sequence for a model
# Number here has unique constraint resulting in IntegrityError being thrown
# whenever a duplicate is added. can be useful for working around mysql's lack
# of sequences
def generate_number():
    qs = MyModel.objects.aggregate(last_number=Max(F('card_number')))
    next_number = (qs.get('last_card_number') or 0) + 1
    self.card_number = card_number
    super().save(*args, **kwargs)
retry_fn(generate_number, (IntegrityError, ), 10)
```

### Views 

#### JSONExceptionAPIView

FIXME

### Webpack

#### TimestampWebpackLoader

* Extension of WebpackLoader that appends a `?ts=(timestamp)` query string based on last modified time of chunk to serve.
* Allows static asset web server to send far future expiry headers without worrying about cache invalidation.

* Example usage

```python
WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': 'dist/prod/',
        'STATS_FILE': _Path(PROJECT_DIR, 'frontend/dist/prod/webpack-stats.json'),
        'LOADER_CLASS': 'allianceutils.webpack.TimestampWebpackLoader',
    },
}
```

## Changelog

* Note: `setup.py` reads the highest version number from this section, so use versioning compatible with setuptools 
* 0.3
    * 0.3.x
        * Fix `check_url_trailing_slash` failing with `admin.site.urls`
    * 0.3.1
        * Fix install failure with setuptools<20.3  
    * 0.3.0
        * Breaking Changes
            * Dropped support for python <3.4
            * Dropped support for django <1.11
        * Added `GenericUserProfile`
        * Added `python_to_django_date_format`
        * Added `check_url_trailing_slash`
        * Added `QueryCountMiddleware`
        * Test against python 3.4, 3.5, 3.6
* 0.2
    * 0.2.0
        * Breaking Changes
            * The interface for `get_autodump_labels` has changed 
        * Added autodumpdata SQL output format
        * Added `mysqlquickdump` options `--model` and `--explicit` 
        * Update to work with webpack_loader 0.5
* 0.1
    * 0.1.6
        * Update `json_orminheritancefix` to work with django 1.11 
    * 0.1.5
        * Fix missing import if using autodumpdata automatically calculated filenames
        * autodumpdata now creates missing fixture directory automatically
    * 0.1.4
        * Fix bad versioning in previous release
    * 0.1.3
        * Added autodumpdata test cases
        * Added autodumpdata `--stdout`, `--output` options
        * Fix autodumpdata failing if `settings.SERIALIZATION_MODULES` not defined
    * 0.1.2
        * Added test cases, documentation
    * 0.1.1
        * Added `StaticStorage`, `MediaStorage`
    * 0.1.0
        * Initial release
