{
  "action": ["create"],
  "principal": ["*"],
  "effect": "allow",
  "condition": "belongs_to_operator",
}

def belongs_to_operator(self, request, view, action) -> bool:
  # check that we are creating an object that will belong to
  # an operator


Another idea:
Scopes by defining nested routes

/users/{user_pk}/workschedules/{workschedule_pk}/workslots/{workslot_pk}
/operators/{operator_pk}/workschedules/{workschedule_pk}/workslots/{workslot_pk}
/productionlines/{productionline_pk}/workschedules/{workschedule_pk}/workslots/{workslot_pk}

Enforcement may now simply be based on the url... ;)
