	
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
			if hasattr(v, "ToDict"):
				rawList.append(v.ToDict())
			else:
				rawList.append(v)

		data["{{prop.json}}"] = rawList
		{% elif prop.IsMap() %}
		rawSubmap = {}
		for k, v in self.{{prop.name}}_.items():
			if hasattr(v, "ToDict"):
				rawSubmap[k] = v.ToDict()
			else:
				rawSubmap[k] = v

		data["{{prop.json}}"] = rawSubmap
		{% else %}
	
		if self.{{prop.name}}_ is not None and hasattr(self.{{prop.name}}_, "ToDict"):
			data["{{prop.json}}"] = self.{{prop.name}}_.ToDict()
		else:
			data["{{prop.json}}"] = self.{{prop.name}}_
	
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
					if hasattr(ud, "FromDict"):
						ud.FromDict(rw)
					else:
						ud = rw
					res.append(ud)

				self.{{prop.name}}_ = res
				{% elif prop.IsMap() %}
				res = {{ prop.default }}
				
				for rk, rw in rawValue.items():
					ud = {{prop.ComplexTypeValueDefault()}}
					if hasattr(ud, "FromDict"):
						ud.FromDict(rw)
					else:
						ud = rw
					res[rk] = ud

				self.{{prop.name}}_ = res
				{% else %}
				if hasattr(self.{{prop.name}}_, "FromDict"):
					self.{{prop.name}}_.FromDict(rawValue)
				else:
					self.{{prop.name}}_ = rawValue
				
				{% endif %}
			{% endfor %}
		
	