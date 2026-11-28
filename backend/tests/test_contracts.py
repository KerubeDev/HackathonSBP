import pytest
from pydantic import ValidationError
from app.contracts import RunRequest

def test_request_defaults_to_v1():
    assert RunRequest(query="show data").api_version == "v1"

def test_request_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        RunRequest(query="show data", unknown=True)
