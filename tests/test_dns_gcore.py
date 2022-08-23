import json
import pytest
import responses

from certbot_dns_gcore.dns_gcore import _GCoreClient
from tests.conftest import txt_data_expected1, txt_data_expected2


@pytest.mark.parametrize('kwargs', ({'token': None}, {'login': 'user'}, {'password': 'test'}))
def test_gcoreclient_fail(kwargs):
    # check
    with pytest.raises(ValueError):
        _GCoreClient(**kwargs)


@responses.activate
@pytest.mark.parametrize('kwargs', ({'token': '123'}, {'login': 'user', 'password': 'test'}))
def test_add_txt_record_success(kwargs, record_payload, mock_auth, mock_get_zones, mock_post_record):
    # act # check
    assert _GCoreClient(**kwargs).add_txt_record(**record_payload) is None


@responses.activate
def test_update_txt_record_no_duplicates(record_payload, mock_auth, mock_dns_api, rrset_exists_two_records, kwargs={'token': '123'}):
    _GCoreClient(**kwargs).add_txt_record(**record_payload)
    # post
    assert mock_dns_api.calls[1].request.body == b'{"resource_records": [{"content": ["123456790"], "enabled": true}], "ttl": 300}'
    # post: should get conflict on post
    assert mock_dns_api.calls[1].response.status_code == 409
    # get: should get 2 records
    assert mock_dns_api.calls[2].response._content == b'{"resource_records": [{"content": ["coexisting content"], "enabled": true}, {"content": ["123456790"], "enabled": true}], "ttl": 300}'
    # put: expect the original payload (no duplicate) in put request not to cause _two or more records have same content_ dnsapi error
    # could have checked count only, but comparing original content with payload
    assert sorted(json.loads(mock_dns_api.calls[3].request.body).items()) == sorted(json.loads(rrset_exists_two_records).items())


@responses.activate
@pytest.mark.parametrize('kwargs', ({'token': '123'}, {'login': 'user', 'password': 'test'}))
def test_del_txt_record_success(kwargs, record_payload, mock_auth, mock_get_zones, mock_get_record, mock_del_record):
    # init
    record_payload.pop('record_content')
    record_payload.pop('record_ttl')

    # act # check
    assert _GCoreClient(**kwargs).del_txt_record(**record_payload) is None


@pytest.mark.parametrize('in_data, out_data', (
    (['text'], txt_data_expected1()), (['text1', 'text2'], txt_data_expected2()),
))
def test_data_for_txt(in_data, out_data):
    # check
    assert _GCoreClient._data_for_txt(300, in_data) == out_data


@responses.activate
@pytest.mark.parametrize('subdomain', ('test1.example.com', 'test2.test1.example.com', 'test3.test2.test1.example.com'))
def test_find_zone_name_success(record_payload, subdomain, mock_auth, mock_get_zones):
    # check
    assert _GCoreClient(token='test')._find_zone_name(subdomain) == record_payload['domain']
