	
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

		data["{{prop.json}}"] = rawList
		{% elif prop.IsMap() %}
		rawSubmap = {}
		for k, v in self.{{prop.name}}_.items():
			{% if prop.IsComplexType() %}
			rawSubmap[k] = v.ToDict()
			{% else %}
			rawSubmap[k] = v
			{% endif %}

		data["{{prop.json}}"] = rawSubmap
		{% else %}
		
		{% if prop.IsComplexType() %}
		# if self.{{prop.name}}_ is not None:
		data["{{prop.json}}"] = self.{{prop.name}}_.ToDict()
		{% else %}
		data["{{prop.json}}"] = self.{{prop.name}}_
		{% endif %}
	
		{% endif %}
		{% endfor %}
		return data
	

	def FromDict(self, data):
		for key, rawValue in data.items():
			if rawValue is None:
				continue
			
			{% for prop in data.properties %}
			if key == "{{prop.json}}":
				{% if prop.IsArray() %}
				res = {{ prop.default }}

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
				res = {{ prop.default }}
				
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
		
	