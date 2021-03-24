## Making scope definition more declarative (this is important for maintainability)

The idea is nicely explained in the following quote from https://github.com/rsinger86/drf-access-policy
	"No more digging through views or seralizers to understand access logic -- it's all in one place in a format that less technical stakeholders can understand."

Most scope enforcement now follows a certain pattern. A scope is mostly defined in terms of two aspect:

- The subset of the models that may be operated on
- A subset of the fields that may be operated on

The first aspect may be conveniently defined by using querysets. However, the enforcement of this may be a little bit involved. However, having this logic in one single place and with a well-defined behavior is preferable over a lot of duplicate code.

The second aspect may be less complex to enforce. Currently, these checks are of the form:
```python
def _scope_change_project(self, request, obj, values):
	return set(values) <= {'id', 'project'}
```
This may easily be generalized by some `writable_fields` or `readonly_fields` list, similar to what is actually happening in django-rest-framework's `ModelSerializer` class (https://www.django-rest-framework.org/api-guide/serializers/#specifying-read-only-fields).

See the concept class `DynamicScopeMixin` with some examples of the API that we propose.

Another (rather radical idea) is to use the concept of a Serializer (https://www.django-rest-framework.org/api-guide/serializers/) for converting a request into an actual object. The validation in a serializer can be made such that it enforces a scope. You may define a serializer for a scope which then checks if you only provided the values that you are allowed to set in the given scope.

Views are controlling access to which objects are accessible (aspect 1)
Serializers are controlling access to fields of a model (aspect 2).
Object level permissions are controlling what we call 'scope's. See https://rsinger86.github.io/drf-access-policy/object_level_permissions/.

If we were to use drf-access-policy, then we could do something like this
```python
{
  # only allow users to add this kind of model for operators
  "action": ["post"],
  "principal": ["*"],
  "effect": "allow",
  "condition": ["user_must_have_scope:name_of_scope", "belongs_to:operator"],
}

def user_must_have_scope(self, request, view, action, field: str) -> bool:
	# check that the user has the required scope

def belongs_to(self, request, view, action, field: str) -> bool:
  # check that we are creating an object that will belong to the specified relation
```

You would tell to the serializer to which other object (operator, productionline, user) the newly created model will belong, by just setting the appropriate pk. The serializer then makes sure that you only assign it to this specific relation.

Checking if the user is allowed to do this assignment can be done by defining a custom permission and implementing the `.has_permission(self, request, view)` method.

```python
class CreateWorkSlotForOperatorPermission(BasePermission):

	def has_permission(self, request, view):
		# check if the supplied data has only the operator relation set.

See https://stackoverflow.com/questions/34860988/django-rest-framework-restricting-user-access-for-objects
https://www.django-rest-framework.org/tutorial/4-authentication-and-permissions/


## Making scope enforcement more dynamic (this is more about implementation)

We could define the enforcement of scopes for a particular action more dynamically, and thereby also allowing custom methods to be easily defined, in the following way:

For every method, we require two functions:
```python
scope_func(scope, request, *args, **kwargs)
combine_func(result1, result2)
```
The scope function may implement the check for a particular scope. The combine function defines how the resulsts of the scope functions for multiple scopes are combined. For example, the view scope functions may now be combined by a simple `|` operation and the other scope functions may be combined by a simple `OR` operation. In this way, we may simply use the `reduce` function on the list of return values.

For example, for the view method, this may look like this:
```python
if action_type == 'view':
	scope_func = self.scope_view
	# we take the union of the resulting queries
	combine_func = lambda: scope_query, q: q | scope_query
```


A possible implementation would go something like this:
```python
def check_scope(self, action_type, request, **kwargs):
    """
    Check if the current user has the required scope(s) to perform the
    given action.
    """

    # get the scopes that the current user has for `action_type`
    user_scopes = self._require_model_perm(action_type, request)

    # Select the function that checks a particular scope for the method type
    # and the function that combines their return values.
    # For the scope functions that return a boolean, we just 'reduce' their
    # values with a simple OR operation.
    # You may change this to AND if you want to enforce that every scope of a user allows
    # needs to grant access.
    if action_type == 'view':
        scope_func = self.scope_view
        # we take the union of the resulting queries
        combine_func = lambda: scope_query, q: q | scope_query
    elif action_type == 'add':
        scope_func = self.scope_add
        combine_func = operators.or_
    elif action_type == 'change':
        scope_func = self.scope_change
        combine_func = operators.or_
    elif action_type == 'delete':
        scope_func = self.scope_delete
        combine_func = operators.or_
    else:
        # see if custom methods are defined
        try:
            scope_func, combine_func = self.custom_method_scope_funcs[action_type]
        except Exception:
            raise Exception('Scoping for custom method {} is not implemented. The '
                            '`custom_method_scope_funcs` dict does not contain key {}'.format(action_type))

    # execute the scope enforcement function for every user scope
    results = map(scope_func, user_scopes)
    result = reduce(combine_func, results)

    # if the result is a boolean, we just check if it is true
    # otherwise, we just return the computed value (queryset in the case of a view request)
    if isinstance(result, bool) and not result:
        raise ScopingError(
                user=request.user,
                perm='You do not have a scope that allows you to perform action {} on model {}.'.format(action_type, self.model)
        )
    else:
        return result
```
