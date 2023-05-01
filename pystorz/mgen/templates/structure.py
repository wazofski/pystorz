 

def {{ data.name }}Factory():
	ret = _{{ data.name }}()
	{% for prop in data.properties %}
	ret.{{ prop.name }}_ = {{ prop.default }}{% endfor %}
	
	return ret


class _{{ data.name }}({{data.implements}}):

	def __init__(self):
		{% for prop in data.properties %}
		self.{{ prop.name }}_ = {{prop.default}}{% endfor %}

	{% for prop in data.properties %}
	{% if prop.name != "External" %}

	def Set{{ prop.name }}(self, val):
		{% if prop.type == "datetime" %}
		self.{{ prop.name }}_ = utils.datetime_string(val)
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
		return utils.datetime_parse(self.{{ prop.name }}_)
		{% else %}
		return self.{{ prop.name }}_
		{% endif %}

	{% endif %}
	{% endfor %}

	def Clone(entity):
		return utils.clone_object(entity, Schema())

