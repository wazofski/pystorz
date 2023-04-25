<p align="center">
<img src="logo.png" width="300" alt="storz" />
</p>

**pystorz** is an *object store framework* built in python. It consists of a set of modules implementing the [Store](https://github.com/wazofski/pystorz/tree/master/pystorz/store) interface and features a simple [object modeling language](https://github.com/wazofski/pystorz/tree/master/pystorz/mgen) used to generate golang object class meta for interacting with `Store` APIs.

**pystorz** modules provide functionality to store, modify and retrieve modeled objects from various sources (TBD). Such modules can be composed together to chain `Store` functionality into more complex logical modules. Combining modules allows handling object changes and manipulating data in complex ways *within or across* services, making multi-level server complexity achievable with ease. The Store modules are fully compatible with each other and can be composed in any combination since they all implement or expose the same [Store](https://github.com/wazofski/pystorz/tree/master/pystorz/store) interface.

Original storz was written in go. You can check it out here:
[https://github.com/wazofski/gostorz](https://github.com/wazofski/gostorz)

This is a python port of the original storz.
Still in development.

## Quick Start Guide

### Installation
```
pip install pystorz
```

## Model example

You can find a saomple model in the tests folder.
[https://github.com/wazofski/pystorz/blob/master/tests/model/sample.yml](https://github.com/wazofski/pystorz/blob/master/tests/model/sample.yml)

You can define simple structures and reference them as fields in other structures.

You need to define Objects that will become your root level modeled objects. You can then create, update, delete and retrieve these from using a store.

Only a SQLite store is implemented at the moment.

More to come.
Check out the go version (link above) for more information.

## Usage
```
    from pystorz.mgen import builder

    # run the code gen to 
    builder.Generate("path/to/model.yml")
    # this will make a generated folder in the project home directory

    # you can then import the generated model
    from generated import model

    # initialize a store
    stor = SqliteStore(
        Schema(),
        SqliteConnection("path/to/your/sqlite3.db"))

    world = model.WorldFactory()
    world.External().SetName("hello")

    created_world = stor.Create(world)
    world.External().SetDescription("hello world")
    updated_world = stor.Update(world.Metadata().Identity(), world)
    
    # ...

```
