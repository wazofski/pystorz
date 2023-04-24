<p align="center">
<img src="logo.png" width="300" alt="storz" />
</p>

**pystorz** is an *object store framework* built in python. It consists of a set of modules implementing the [Store](https://github.com/wazofski/pystorz/tree/main/src/store) interface and features a simple [object modeling language](https://github.com/wazofski/pystorz/tree/main/src/mgen) used to generate golang object class meta for interacting with `Store` APIs.

**pystorz** modules provide functionality to store, modify and retrieve modeled objects from various sources (TBD). Such modules can be composed together to chain `Store` functionality into more complex logical modules. Combining modules allows handling object changes and manipulating data in complex ways *within or across* services, making multi-level server complexity achievable with ease. The Store modules are fully compatible with each other and can be composed in any combination since they all implement or expose the same [Store](https://github.com/wazofski/storz/tree/main/src/store) interface.

## Quick Start Guide

### Installation
```
pip install pystorz
```