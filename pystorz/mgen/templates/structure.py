 

def {{ data.name }}Factory() -> {{ data.name }}:
	ret = _{{ data.name }}()
	{% for prop in data.properties %}
	ret.{{ prop.name }}_ = {{ prop.default }}{% endfor %}
	
	return ret


class _{{ data.name }}({{data.name}}):

	def __init__(self):
		{% for prop in data.properties %}
		self.{{ prop.name }}_ = {{prop.default}}{% endfor %}

	{% for prop in data.properties %}

	def Set{{ prop.name }}(self, val):
		{% if prop.type == "datetime" %}
		self.{{ prop.name }}_ = store.datetime_string(val)
		{% elif prop.type == "string" %}
		self.{{ prop.name }}_ = str(val)
		{% elif prop.type == "int" %}
		self.{{ prop.name }}_ = int(val)
		{% elif prop.type == "float" %}
		self.{{ prop.name }}_ = float(val)
		{% elif prop.type == "bool" %}
		self.{{ prop.name }}_ = bool(val)
		{% else %}
		self.{{ prop.name }}_ = val
		{% endif %}

	def {{ prop.name }}(self):
		{% if prop.type == "datetime" %}
		return store.datetime_parse(self.{{ prop.name }}_)
		{% else %}
		return self.{{ prop.name }}_
		{% endif %}

	{% endfor %}

