rm -rf .pytest_cache

pytest -v test_mgen.py -cov --cov-report=html
pytest -v -k "thestore" test_common.py -cov --cov-report=html
