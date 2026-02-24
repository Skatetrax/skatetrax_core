import pytest

def test_import_uSkaterMeta():
    try:
        from skatetrax.models.t_skaterMeta import uSkaterConfig
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")
    assert hasattr(uSkaterConfig, "__tablename__")