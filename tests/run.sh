rm -rf .pytest_cache

pytest -v test_mgen.py
pytest -v -k "thestore" test_common.py
