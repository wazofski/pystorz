 

class _Schema:
	def __init__(self, objects):
		self.objects = objects
	
	def ObjectForKind(self, kind):
		{% for r in data["resources"] %}
		
		if kind == "{{r.name}}":
			return {{r.name}}Factory()
		elif kind == "{{r.IdentityPrefix()}}":
			return {{r.name}}Factory()

		{% endfor %}
		
		return None
	
	def types(self):
		return self.objects

def Schema():
	objects = [
		{% for r in data["resources"] %}
		"{{r.name}}",
		{% endfor %}
	]

	return _Schema(objects)

 