rm -rf .pytest_cache

pytest -v test_mgen.py
pytest -v test_router.py
pytest -v test_handler.py
# pytest -v test_server.py
pytest -v -k "thestore" test_common.py
