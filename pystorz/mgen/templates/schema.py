 

class _Schema(store.SchemaHolder):
	def __init__(self, objects):
		self.objects = objects
	
	def ObjectForKind(self, kind) -> store.Object:
		{% for r in data["resources"] %}
		
		if kind == "{{r.name}}":
			return {{r.name}}Factory()
		elif kind == "{{r.IdentityPrefix()}}":
			return {{r.name}}Factory()

		{% endfor %}
		
		raise Exception(constants.ErrNoSuchObject)
	
	def Types(self):
		return self.objects

def Schema():
	objects = [
		{% for r in data["resources"] %}
		"{{r.name}}",
		{% endfor %}
	]

	return _Schema(objects)

 