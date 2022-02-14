import pytest


@pytest.fixture
def record_payload():
    return {
        'domain': 'example.com',
        'record_name': '_acme-challenge.example.com',
        'record_content': '123456790',
        'record_ttl': 300
    }

@pytest.fixture
def txt_data_payload():
    return {"resource_records": [{"content": ['text'], "enabled": True}], "ttl": 300}
