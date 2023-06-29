import json
from pystorz.internal import constants
# "from pystorz.store import utils",
from pystorz.store import store
from datetime import datetime
from typing import Type


{% for data in structs %}

class {{ data.name }}:

	def __init__(self):
		raise Exception("cannot initialize like this. use the factory method")
	
	def ToDict(self):
		raise Exception("not implemented")

	def FromDict(self, data):
		raise Exception("not implemented")

{% for prop in data.properties %}
	def {{ prop.CapitalizedName() }}(self) -> {{ prop.StrippedType() }}:
		raise Exception("not implemented")

	def Set{{ prop.CapitalizedName() }}(self, val: {{prop.StrippedType()}}):
		raise Exception("not implemented")
{% endfor %}


def {{ data.name }}Factory() -> {{ data.name }}:
	ret = _{{ data.name }}()
	{% for prop in data.properties %}
	ret.{{ prop.name }}_ = {{ prop.Default() }}
	{% endfor %}
	return ret


class _{{ data.name }}({{data.name}}):

	def __init__(self):
		{% for prop in data.properties %}
		self.{{ prop.name }}_ = {{prop.Default()}}
		{% endfor %}

	{% for prop in data.properties %}
	def Set{{ prop.CapitalizedName() }}(self, val):
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

	def {{ prop.CapitalizedName() }}(self):
		{% if prop.type == "datetime" %}
		return store.datetime_parse(self.{{ prop.name }}_)
		{% else %}
		return self.{{ prop.name }}_
		{% endif %}

	{% endfor %}

	
	def FromJson(self, jstr):
		data = json.loads(jstr)
		return self.FromDict(data)


	def ToJson(self):
		return json.dumps(self.ToDict())


	def ToDict(self):
		data = {}
		{% for prop in data.properties %}
		{% if prop.IsArray() %}
		rawList = []
		for v in self.{{prop.name}}_:
			{% if prop.IsComplexType() %}
			rawList.append(v.ToDict())
			{% else %}
			rawList.append(v)
			{% endif %}

		data["{{prop.name}}"] = rawList
		{% elif prop.IsMap() %}
		rawSubmap = {}
		for k, v in self.{{prop.name}}_.items():
			{% if prop.IsComplexType() %}
			rawSubmap[k] = v.ToDict()
			{% else %}
			rawSubmap[k] = v
			{% endif %}

		data["{{prop.name}}"] = rawSubmap
		{% else %}
		
		{% if prop.IsComplexType() %}
		# if self.{{prop.name}}_ is not None:
		data["{{prop.name}}"] = self.{{prop.name}}_.ToDict()
		{% else %}
		data["{{prop.name}}"] = self.{{prop.name}}_
		{% endif %}
	
		{% endif %}
		{% endfor %}
		return data
	

	def FromDict(self, data):
		for key, rawValue in data.items():
			if rawValue is None:
				continue
			
			{% for prop in data.properties %}
			if key == "{{prop.name}}":
				{% if prop.IsArray() %}
				res = {{ prop.Default() }}

				for rw in rawValue:
					ud = {{ prop.ComplexTypeValueDefault() }}
					{% if prop.IsComplexType() %}
					ud.FromDict(rw)
					{% else %}
					ud = rw
					{% endif %}
					res.append(ud)

				self.{{prop.name}}_ = res
				{% elif prop.IsMap() %}
				res = {{ prop.Default() }}
				
				for rk, rw in rawValue.items():
					ud = {{prop.ComplexTypeValueDefault()}}
					{% if prop.IsComplexType() %}
					ud.FromDict(rw)
					{% else %}
					ud = rw
					{% endif %}
					res[rk] = ud

				self.{{prop.name}}_ = res
				{% else %}
				{% if prop.IsComplexType() %}
				self.{{prop.name}}_.FromDict(rawValue)
				{% else %}
				self.{{prop.name}}_ = rawValue
				{% endif %}
				
				{% endif %}
			{% endfor %}
		
{% endfor %}


{% for _, data in resources.items() %}

{% if data.external %}
class {{ data.name }}(store.ExternalHolder):
{% else %}
class {{ data.name }}(store.Object):
{% endif %}

	def __init__(self):
		raise Exception("cannot initialize like this. use the factory method")
	
	def ToDict(self):
		raise Exception("not implemented")

	def FromDict(self, data):
		raise Exception("not implemented")

	def Clone(self) -> Type["{{data.name}}"]:
		raise NotImplementedError()

	def Meta(self) -> store.Meta:
		raise Exception("not implemented")

	{% if data.external %}
	def External() -> {{ data.external }}:
		raise Exception("not implemented")

	{% endif %}

	{% if data.internal %}
	def Internal(self) -> {{ data.internal }}:
		raise Exception("not implemented")

	{% endif %}



def {{ data.name }}Factory() -> {{ data.name }}:
	ret = _{{ data.name }}()

	{% if data.external %}
	ret.external_ = {{ data.external }}Factory()
	{% endif %}
	{% if data.internal %}
	ret.internal_ = {{ data.internal }}Factory()
	{% endif %}

	return ret


class _{{ data.name }}({{data.name}}):

	def __init__(self):
		self.meta_ = store.MetaFactory("{{ data.name }}")
		self.external_ = None
		self.internal_ = None

	{% if data.external %}
	def SetExternal(self, val):
		self.external_ = val

	def External(self) -> {{ data.external }}:
		return self.external_

	{% endif %}

	{% if data.internal %}
	def SetInternal(self, val):
		self.internal_ = val
	
	def Internal(self) -> {{ data.internal }}:
		return self.internal_

	{% endif %}

	
	def FromJson(self, jstr):
		data = json.loads(jstr)
		return self.FromDict(data)


	def ToJson(self):
		return json.dumps(self.ToDict())


	def ToDict(self):
		data = {}
		data["metadata"] = self.meta_.ToDict()
		{% if data.external %}data["external"] = self.external_.ToDict(){% endif %}
		{% if data.internal %}data["internal"] = self.internal_.ToDict(){% endif %}
		return data


	def FromDict(self, data):
		for key, rawValue in data.items():
			if rawValue is None:
				continue
			
			if key == "metadata":
				self.meta_.FromDict(rawValue)

			{% if data.external %}
			if key == "external":
				self.external_.FromDict(rawValue)
			{% endif %}

			{% if data.internal %}
			if key == "internal":
				self.internal_.FromDict(rawValue)
			{% endif %}
	
	def Clone(self) -> {{data.name}}:
		ret = {{data.name}}Factory()
		ret.FromJson(self.ToJson())
		return ret

	def Metadata(self) -> store.Meta:
		return self.meta_

	def SetMetadata(self, val: store.Meta):
		self.meta_ = val

	def PrimaryKey(self):
		return str(self.{{data.PrimaryKeyFunctionCaller()}})


def {{data.name}}Identity(pkey):
	return store.ObjectIdentity("{{ data.IdentityPrefix() }}/" + pkey )

{{data.name}}KindIdentity = store.ObjectIdentity("{{ data.IdentityPrefix() }}/")

{{data.name}}Kind = "{{ data.name }}"


{% endfor %}


 

class _Schema(store.SchemaHolder):
	def __init__(self, objects):
		self.objects = objects
	
	def ObjectForKind(self, kind) -> store.Object:
		{% for _, r in resources.items() %}
		
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
		{% for _, r in resources.items() %}
		"{{r.name}}",
		{% endfor %}
	]

	return _Schema(objects)

 