import pytest
import responses
from responses import matchers
import json

from certbot_dns_gcore.api_gcore import GCoreClient


@pytest.fixture
def record_payload():
    return {
        'domain': 'example.com',
        'record_name': '_acme-challenge.example.com',
        'record_content': '123456790',
        'record_ttl': 300
    }


@pytest.fixture
def rrset_exists_two_records():
    return '''\
{
    "resource_records": [
        {
            "content": [
                "coexisting content"
            ],
            "enabled": true
        },
        {
            "content": [
                "123456790"
            ],
            "enabled": true
        }
    ],
    "ttl": 300
}'''


def txt_data_expected1():
    return {'resource_records': [{'content': ['text'], 'enabled': True}], 'ttl': 300}


def txt_data_expected2():
    return {'resource_records': [{'content': ['text1'], 'enabled': True}, {'content': ['text2'], 'enabled': True}], 'ttl': 300}


@pytest.fixture
def mock_auth():
    # auth
    responses.add(
        responses.POST,
        f'{GCoreClient._auth_url}/auth/jwt/login',
        json={'access': 'token'},
        status=200
    )


@pytest.fixture
def mock_get_zone(record_payload):
    # check domain
    responses.add(
        responses.GET,
        f'{GCoreClient._dns_api_url}/{GCoreClient._root_zones}/{record_payload["domain"]}',
        json={'name': record_payload["domain"]},
        status=200
    )

@pytest.fixture
def mock_get_zones(record_payload):
    domain_2_level = '.'.join(record_payload["domain"].split('.')[-2:])
    params = {'limit': '100', 'name': domain_2_level}
    responses.add(
        responses.GET,
        f'{GCoreClient._dns_api_url}/{GCoreClient._root_zones}',
        match=[responses.matchers.query_param_matcher(params)],
        json={'zones': [{'name': record_payload["domain"]}]},
        status=200
    )

@pytest.fixture
def mock_del_record(record_payload):
    # del
    responses.add(
        responses.DELETE,
        f'{GCoreClient._dns_api_url}/{GCoreClient._root_zones}/{record_payload["domain"]}/{record_payload["record_name"]}/TXT',
        json={}, status=200
    )


@pytest.fixture
def mock_get_record(record_payload):
    # check record
    responses.add(
        responses.GET,
        f'{GCoreClient._dns_api_url}/{GCoreClient._root_zones}/{record_payload["domain"]}/{record_payload["record_name"]}/TXT',
        json={}, status=200
    )


@pytest.fixture
def mock_post_record(record_payload):
    # check record
    responses.add(
        responses.POST,
        f'{GCoreClient._dns_api_url}/{GCoreClient._root_zones}/{record_payload["domain"]}/{record_payload["record_name"]}/TXT',
        json={},
        status=200
    )


@pytest.fixture
def mock_dns_api(record_payload, rrset_exists_two_records, mock_get_zones):
    responses.add(
        responses.POST,
        f'{GCoreClient._dns_api_url}/{GCoreClient._root_zones}/{record_payload["domain"]}/{record_payload["record_name"]}/TXT',
        json={},
        status=409
    )
    responses.add(
        responses.GET,
        f'{GCoreClient._dns_api_url}/{GCoreClient._root_zones}/{record_payload["domain"]}/{record_payload["record_name"]}/TXT',
        json=json.loads(rrset_exists_two_records),
        status=200
    )
    responses.add(
        responses.PUT,
        f'{GCoreClient._dns_api_url}/{GCoreClient._root_zones}/{record_payload["domain"]}/{record_payload["record_name"]}/TXT',
        json={},
        status=200
    )
    yield responses
