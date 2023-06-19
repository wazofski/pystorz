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
- add mysql store (high) @done
- fix mysql list and get autocommit issue @done
- mysql auto-reconnect @done

- the factory must return the interface type @done
- generated model flake compatibility @done
- make the intellisence work @done

- router store (high) @done

- add argument and return types to all stores @done
    - interface adn implementations @done

- fix mgen dependency issues @done

- add common test for complex datetime filtering (high)
- intellisense - full return and argument types for lists and maps

- github
    - project (high)
    - documentation (high)

    - links
        - https://pypi.org/project/pystorz/
        - https://github.com/wazofski/pystorz

- behavior store (high)

- add enums ?
- store migration tool
- object browser

- autoconfig
    - DB init
    - object config

- in memory store
- cache store
- mongo store
