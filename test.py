from mgen.builder import Generate
from mgen.test import test_mgen

def test_mgen_can_generate():
    err = Generate("test/model")
    
    assert err is None

test_mgen_can_generate()
test_mgen()
