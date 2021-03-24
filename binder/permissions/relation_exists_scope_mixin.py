

class RelationExistsScopeMixin:
	"""
	Specify dynamic scopes based on the existance of a relation to
	another model.

	This may be useful if you have a model that may belong to multiple
	other types of models and you want to restrict the user into modifying
	only models that must belong to one specific type of model.

	Use the dictionary `relation_scopes` to specify the path (in Django
	queryset notation) to the relation to check for existance.

	Suppose, for example, that we want to scope access to payslips
	based on if they belong to a factory operator or an office clerk.
	We may define the two scopes as follows:

		relation_scopes = {
			'belongs_to_clerk': 'clerk',
			'belongs_to_operator': 'operator',
		}

	Relationships spanning multiple models are also possible:

		relation_scope = {
			'belongs_to_operator_which_belongs_to_external_company': 'operator__external_company',
		}

	"""

	def _dynamic_scope_func(self, action_type, scope, request, *args):
		# we only support basic crud at the moment
		if action_type not in ['view', 'add', 'change', 'delete']:
			raise BinderException('Scoping for custom methods (other than basic crud) is not yet implemented.')

		# first check if the given scope is actually defined
		if scope in relation_scopes:
			path = relation_scopes[scope]
		else:
			raise UnexpectedScopeException(
				'Scope {} is not implemented for model {}'.format(scope, self.model))

		# then call the appropriate scope enforcement function
		if action_type == 'view':
			return self._scope_view(path, request)
		else:
			return getattr(self, '_scope_' + action_type)(path, request, *args)



	def _scope_view(self, path, request):
		kwargs = {
			path + '__isnull': False
		}
		# this will translate to `Q(path__to__some__relation__isnull=False)`
        return Q(**kwargs)



    def _scope_add(self, path, request, obj, values):
		try:
			# Nested try-statements because obj.work_schedule can also throw a
			# WorkSchedule.DoesNotExist
			try:
				work_schedule = WorkSchedule.objects.get(
					pk=values['work_schedule'],
				)
			except KeyError:  # No work schedule supplied
				work_schedule = obj.work_schedule
		except WorkSchedule.DoesNotExist:
			return True  # Leave for validation

		return work_schedule.operator is not None



	def _scope_delete(self, path, request, obj, values):
        return obj.work_schedule.operator user user is not None



    def _scope_change(self, path, request, obj, values):
        return (
            self._scope_delete(path, request, obj, values) and
            self._scope_add(path, request, obj, values)
        )
