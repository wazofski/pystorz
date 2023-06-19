
	def Clone(self) -> {{data.name}}:
		ret = {{data.name}}Factory()
		ret.FromJson(self.ToJson())
		return ret

