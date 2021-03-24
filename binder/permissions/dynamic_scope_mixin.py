# CONCEPT

class DynamicScopeMixin:
	"""
	The purpose of this class is to support defining scopes in a declarative way,
	instead of via the imperative enforcement that we have currently.

	The idea is that you are able to define most scopes in terms of a queryset,
	which basically just defines a subset of the object instances.
	"""

	scopes = {
		'operator': Q(work_schedule__operator__isnull=False)

		# or when you want to have some more control:
		'current': lambda request: return (
			Q(work_schedule__operator__isnull=False) &
			Q(work_schedule__start_date__gte=timezone.now().date())
		)

		# or by just referencing the function
		'own': self._scope_view_own,

		'own': lambda request: (
			if not request.user.is_anonymous:
				'user=request.user'
			elif request.user.is_operator:
				'operator=request.user.operator'
			else:
				return none
		),

		'own': Q(work_schedule__user__isnull=False),

		# combining other scopes with AND
		'user_current' : [ 'user', 'current' ],
	}

	def _scope_func(self, action_type, scope, request, *args):
		"""
		Check one particular scope.
		"""

		# get the definition of this scope
		scope_definition = self.scopes[scope]

		# if it's a list, we just combine with AND
		if isinstance(scope_definition, list):
			if action_type == 'view':
				raise BinderException('Composed scopes is not yet implemented for the view method')

			for sub_scope in scope_definition:
				if not self._scope_func(action_type, sub_scope, request, *args):
					return False

			# all scopes in the combination yielded true
			return True

		# execute the defined checks

		# this is were the magic is supposed to happen
