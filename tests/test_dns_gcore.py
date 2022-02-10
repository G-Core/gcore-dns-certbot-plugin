import pytest
import responses

from certbot_dns_gcore.api_gcore import GCoreClient
from certbot_dns_gcore.dns_gcore import _GCoreClient


@pytest.mark.parametrize('kwargs', ({'token': None}, {'login': 'user'}, {'password': 'test'}))
def test_gcoreclient_fail(kwargs):
    # CHECK
    with pytest.raises(ValueError):
        _GCoreClient(**kwargs)


@responses.activate
@pytest.mark.parametrize('kwargs', ({'token': '123'}, {'login': 'user', 'password': 'test'}))
def test_add_txt_record_success(kwargs, record_payload):
    # INIT
    responses.add(
        responses.POST,
        f'{GCoreClient._auth_url}auth/jwt/login',
        json={'access': 'token'},
        status=200
    )
    responses.add(
        responses.POST,
        f'{GCoreClient._dns_api_url}zones/{record_payload["domain"]}/{record_payload["record_name"]}/TXT',
        json={}, status=200
    )

    # ACT # CHECK
    assert _GCoreClient(**kwargs).add_txt_record(**record_payload) is None


@responses.activate
@pytest.mark.parametrize('kwargs', ({'token': '123'}, {'login': 'user', 'password': 'test'}))
def test_del_txt_record_success(kwargs, record_payload):
    # INIT
    record_payload.pop('record_content')
    record_payload.pop('record_ttl')
    responses.add(
        responses.POST,
        f'{GCoreClient._auth_url}auth/jwt/login',
        json={'access': 'token'},
        status=200
    )
    responses.add(
        responses.DELETE,
        f'{GCoreClient._dns_api_url}zones/{record_payload["domain"]}/{record_payload["record_name"]}/TXT',
        json={}, status=200
    )

    # ACT # CHECK
    assert _GCoreClient(**kwargs).del_txt_record(**record_payload) is None


def test_data_for_txt(txt_data_payload):
    assert _GCoreClient._data_for_txt(300, 'text') == txt_data_payload
