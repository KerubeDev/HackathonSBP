import pytest
from pydantic import ValidationError
from app.contracts import RunRequest, UploadConfirmation

def test_request_defaults_to_v1():
    assert RunRequest(query="show data").api_version == "v1"

def test_request_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        RunRequest(query="show data", unknown=True)

def test_upload_confirmation_requires_eight_digit_period():
    assert UploadConfirmation(period="20260930").period == "20260930"
    with pytest.raises(ValidationError):
        UploadConfirmation(period="2026-09")
