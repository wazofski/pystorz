const store = require("pystorz/store");

{% for data in structs %}

class {{ data.name }} {
    constructor() {
        throw new Error("cannot initialize like this. use the factory method");
    }

    ToDict() { throw new Error("not implemented"); }
    FromDict(data) { throw new Error("not implemented"); }

    {% for prop in data.properties %}
    {{ prop.CapitalizedName() }}() { throw new Error("not implemented"); }
    Set{{ prop.CapitalizedName() }}(val) { throw new Error("not implemented"); }
    {% endfor %}
}

function {{ data.name }}Factory() {
    const ret = new _{{ data.name }}();
    {% for prop in data.properties %}
    ret.{{ prop.name }}_ = {{ prop.Default() }};
    {% endfor %}
    return ret;
}

class _{{ data.name }} extends {{data.name}} {
    constructor() {
        super();
        {% for prop in data.properties %}
        this.{{ prop.name }}_ = {{prop.Default()}};
        {% endfor %}
    }

    {% for prop in data.properties %}
    Set{{ prop.CapitalizedName() }}(val) {
        {% if prop.type == "datetime" %}
        this.{{ prop.name }}_ = store.datetime_string(val);
        {% elif prop.type == "string" %}
        this.{{ prop.name }}_ = String(val);
        {% elif prop.type == "int" %}
        this.{{ prop.name }}_ = Number.parseInt(val);
        {% elif prop.type == "float" %}
        this.{{ prop.name }}_ = Number(val);
        {% elif prop.type == "bool" %}
        this.{{ prop.name }}_ = Boolean(val);
        {% else %}
        this.{{ prop.name }}_ = val;
        {% endif %}
    }

    {{ prop.CapitalizedName() }}() {
        {% if prop.type == "datetime" %}
        return store.datetime_parse(this.{{ prop.name }}_);
        {% else %}
        return this.{{ prop.name }}_;
        {% endif %}
    }

    {% endfor %}

    FromJson(jstr) {
        const data = JSON.parse(jstr);
        return this.FromDict(data);
    }

    ToJson() {
        return JSON.stringify(this.ToDict());
    }

    ToDict() {
        const data = {};
        {% for prop in data.properties %}
        {% if prop.IsArray() %}
        const rawList{{prop.name}} = [];
        for (const v of (this.{{prop.name}}_ || [])) {
            {% if prop.IsComplexType() %}
            rawList{{prop.name}}.push(v.ToDict());
            {% else %}
            rawList{{prop.name}}.push(v);
            {% endif %}
        }
        data["{{prop.name}}"] = rawList{{prop.name}};
        {% elif prop.IsMap() %}
        const rawSubmap = {};
        for (const k in (this.{{prop.name}}_ || {})) {
            const v = this.{{prop.name}}_[k];
            {% if prop.IsComplexType() %}
            rawSubmap[k] = v.ToDict();
            {% else %}
            rawSubmap[k] = v;
            {% endif %}
        }
        data["{{prop.name}}"] = rawSubmap;
        {% else %}
        {% if prop.IsComplexType() %}
        data["{{prop.name}}"] = this.{{prop.name}}_ ? this.{{prop.name}}_.ToDict() : null;
        {% else %}
        data["{{prop.name}}"] = this.{{prop.name}}_;
        {% endif %}
        {% endif %}
        {% endfor %}
        return data;
    }

    FromDict(data) {
        for (const key in data) {
            const rawValue = data[key];
            if (rawValue === null || rawValue === undefined) continue;

            {% for prop in data.properties %}
            if (key === "{{prop.name}}") {
                {% if prop.IsArray() %}
                const res = {{ prop.Default() }};

                for (const rw of rawValue) {
                    let ud = {{ prop.ComplexTypeValueDefault() }};
                    {% if prop.IsComplexType() %}
                    ud.FromDict(rw);
                    {% else %}
                    ud = rw;
                    {% endif %}
                    res.push(ud);
                }

                this.{{prop.name}}_ = res;
                {% elif prop.IsMap() %}
                const res = {{ prop.Default() }};

                for (const rk in rawValue) {
                    const rw = rawValue[rk];
                    let ud = {{prop.ComplexTypeValueDefault()}};
                    {% if prop.IsComplexType() %}
                    ud.FromDict(rw);
                    {% else %}
                    ud = rw;
                    {% endif %}
                    res[rk] = ud;
                }

                this.{{prop.name}}_ = res;
                {% else %}
                {% if prop.IsComplexType() %}
                this.{{prop.name}}_.FromDict(rawValue);
                {% else %}
                this.{{prop.name}}_ = rawValue;
                {% endif %}

                {% endif %}
            }
            {% endfor %}
        }
    }
}

{% endfor %}


{% for _, data in resources.items() %}

{% if data.external %}
class {{ data.name }} extends store.ExternalHolder {
{% else %}
class {{ data.name }} extends store.Object {
{% endif %}
    constructor() {
        super();
        throw new Error("cannot initialize like this. use the factory method");
    }

    ToDict() { throw new Error("not implemented"); }
    FromDict(data) { throw new Error("not implemented"); }

    Clone() { throw new Error("not implemented"); }
    Meta() { throw new Error("not implemented"); }

    {% if data.external %}
    External() { throw new Error("not implemented"); }
    {% endif %}

    {% if data.internal %}
    Internal() { throw new Error("not implemented"); }
    {% endif %}
}

function {{ data.name }}Factory() {
    const ret = new _{{ data.name }}();

    {% if data.external %}
    ret.external_ = {{ data.external }}Factory();
    {% endif %}
    {% if data.internal %}
    ret.internal_ = {{ data.internal }}Factory();
    {% endif %}

    return ret;
}

class _{{ data.name }} extends {{data.name}} {
    constructor() {
        super();
        this.meta_ = store.MetaFactory("{{ data.name }}");
        this.external_ = null;
        this.internal_ = null;
    }

    {% if data.external %}
    SetExternal(val) { this.external_ = val; }
    External() { return this.external_; }
    {% endif %}

    {% if data.internal %}
    SetInternal(val) { this.internal_ = val; }
    Internal() { return this.internal_; }
    {% endif %}

    FromJson(jstr) { const data = JSON.parse(jstr); return this.FromDict(data); }
    ToJson() { return JSON.stringify(this.ToDict()); }

    ToDict() {
        const data = {};
        data["metadata"] = this.meta_.ToDict();
        {% if data.external %}data["external"] = this.external_.ToDict(); {% endif %}
        {% if data.internal %}data["internal"] = this.internal_.ToDict(); {% endif %}
        return data;
    }

    FromDict(data) {
        for (const key in data) {
            const rawValue = data[key];
            if (rawValue === null || rawValue === undefined) continue;

            if (key === "metadata") {
                this.meta_.FromDict(rawValue);
            }

            {% if data.external %}
            if (key === "external") { this.external_.FromDict(rawValue); }
            {% endif %}

            {% if data.internal %}
            if (key === "internal") { this.internal_.FromDict(rawValue); }
            {% endif %}
        }
    }

    Clone() {
        const ret = {{data.name}}Factory();
        ret.FromJson(this.ToJson());
        return ret;
    }

    Metadata() { return this.meta_; }
    SetMetadata(val) { this.meta_ = val; }

    PrimaryKey() {
        return String(this.{{data.PrimaryKeyFunctionCaller()}});
    }
}

function {{data.name}}Identity(pkey) {
    return store.ObjectIdentity("{{ data.IdentityPrefix() }}/" + pkey);
}

const {{data.name}}KindIdentity = store.ObjectIdentity("{{ data.IdentityPrefix() }}/");

const {{data.name}}Kind = "{{ data.name }}";

{% endfor %}



class _Schema extends store.SchemaHolder {
    constructor(objects) {
        super();
        this.objects = objects;
    }

    ObjectForKind(kind) {
        {% for _, r in resources.items() %}
        if (kind === "{{r.name}}") return {{r.name}}Factory();
        else if (kind === "{{r.IdentityPrefix()}}") return {{r.name}}Factory();
        {% endfor %}
        throw new Error("object does not exist");
    }

    Types() { return this.objects; }
}

function Schema() {
    const objects = [
        {% for _, r in resources.items() %}
        "{{r.name}}",
        {% endfor %}
    ];
    return new _Schema(objects);
}
