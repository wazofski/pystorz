
	def Metadata(self):
		return self.Meta_

	def PrimaryKey(self):
		return str(self.{{data.primary_key}})


def {{data.name}}Identity(pkey):
	return store.ObjectIdentity("{{ data.IdentityPrefix() }}/" + pkey )

{{data.name}}KindIdentity = store.ObjectIdentity("{{ data.IdentityPrefix() }}/")

{{data.name}}Kind = "{{ data.name }}"
