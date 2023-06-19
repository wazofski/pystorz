
class {{ data["name"] }}({{ data["implements"] }}):

	def __init__(self):
		raise Exception("cannot initialize like this. use the factory method")
	
	def ToDict(self):
		raise Exception("not implemented")

	def FromDict(self, data):
		raise Exception("not implemented")

{% for method, ret in data["methods"] %}
{% if ret|length > 0 %}
	def {{ method }} -> {{ ret }}:
{% else %}
	def {{ method }}:
{% endif %}
		raise Exception("not implemented")

{% endfor %}
