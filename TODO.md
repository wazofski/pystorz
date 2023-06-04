- cursor must be closed?? (high) @done
- fix dependency issue in generated model (high) @done
- add primary key init to metadata.identity by default in loader @done
- add datetime type support (high) @done
- add string encoding to sql content queries (high) @done
- add metadata revision number @done
- do not remove object on update if not necessary (high) @done
    - make a transaction during update and commit once @done
- fix prop filter value decoding to only encode strings (bug) (high) @done
- default datetime value bug (high) @done
- add invalid struct detection in builder (med) @done
- add model prop casting (high) @done
- prop filtering does not work with ordering (bug) (high) @done
- add pkey value check for empty (high) (easy and useful) @done
- map and list of struct is not parsed properly (high) @done
- rename PropFilter to Eq @done
- add complex filtering support (high) @done
    - Lt/Lte @done
    - Gt/Gte @done
    - And/Or/Not @done
    - In @done
- replace the KeyFilter with generic In @done
- delete filtering support (high) @done
- ability to build multiple model directories @done
- web server @done
- web client store @done
- metadata store @done
- remove the functionality from the sql store @done


- test and add common casees for complex filters on datetime types (high)
- add mysql store (high)

- add the rest of the storz    
    - in memory store
    - cache store
    - router store
    - behavior store
    - mongo store


- github documentation (high)
- links
    - https://pypi.org/project/pystorz/
    - https://github.com/wazofski/pystorz

- github project