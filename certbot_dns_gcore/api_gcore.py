"""Wrapper for G-Core DNS API."""

import http
import logging
import re
import typing
import urllib.parse

import requests
from requests import Session

logger = logging.getLogger(__name__)


class GCoreException(Exception):
    """G-Core DNS API client exception."""


class GCoreConflictException(Exception):
    """G-Core DNS API conflict exception."""


class GCoreNotFoundException(Exception):
    """G-Core DNS API conflict exception."""


class GCoreClient:
    """G-Core DNS API client."""

    _root_zones = 'v2/zones'
    _dns_api_url = 'https://api.gcorelabs.com/dns'
    _auth_url = 'https://api.gcorelabs.com/iam'
    _timeout = 10.0
    _error_format = 'Error %s. %s: %r, data: "%r", response: %s'

    def __init__(self, token=None, login=None, password=None, api_url=None, dns_api_url=None, auth_url=None):
        self._session = Session()
        if token is not None:
            self._session.headers.update({'Authorization': f'APIKey {token}'})
        elif login is not None and password is not None:
            token = self._auth(self._auth_url, login, password)
            self._session.headers.update({'Authorization': f'Bearer {token}'})
        else:
            raise ValueError('either token or login & password must be set')
        if api_url:
            self._auth_url = self._build_url(api_url, '/iam')
            self._dns_api_url = self._build_url(api_url, '/dns')
            # more specific parameters should win thus go latter
        if dns_api_url:
            self._dns_api_url = dns_api_url
        if auth_url:
            self._auth_url = auth_url

    def _auth(self, url, login, password):
        """Get auth token."""
        responce = self._session.request(
            'POST',
            self._build_url(url, 'auth', 'jwt', 'login'),
            json={'username': login, 'password': password},
        )
        responce.raise_for_status()
        return responce.json()['access']

    def _request(self, method: str, url: str, params=None, data=None) -> requests.Response or requests.RequestException:
        """Requests handler."""
        responce = self._session.request(method, url, params=params, json=data, timeout=self._timeout)
        if responce.status_code in (  # pylint: disable=R1720
                http.HTTPStatus.BAD_REQUEST, http.HTTPStatus.INTERNAL_SERVER_ERROR,
        ):
            logger.error(self._error_format, responce.status_code, method, url, data or params, responce.text)
            raise GCoreException(responce.text)
        elif responce.status_code == http.HTTPStatus.CONFLICT:
            raise GCoreConflictException(self._error_format % (responce.status_code, method, url,
                                                               data or params, responce.text))
        elif responce.status_code == http.HTTPStatus.NOT_FOUND:
            raise GCoreNotFoundException(self._error_format % (responce.status_code, method, url,
                                                               data or params, responce.text))
        responce.raise_for_status()
        return responce

    def zone(self, zone_name: str, params: dict = None) -> dict:
        """Get DNS zone."""
        return self._request('GET', self._build_url(self._dns_api_url, self._root_zones, zone_name), params).json()

    def zones(self, params: dict = None) -> dict:
        """Get DNS zones."""
        return self._request('GET', self._build_url(self._dns_api_url, self._root_zones), params).json()['zones']

    def zone_create(self, zone_name: str) -> dict:
        """Create DNS zone."""
        return self._request(
            'POST', self._build_url(self._dns_api_url, self._root_zones), data={'name': zone_name},
        ).json()

    def zone_records(self, zone_name: str) -> list:
        """List DNS records from zone."""
        url = self._build_url(self._dns_api_url, self._root_zones, zone_name, 'rrsets')
        rrsets = self._request('GET', url, params={'all': 'true'}).json()
        records = rrsets['rrsets']
        return records

    def record_create(self, zone_name: str, rrset_name: str, type_: str, data: dict) -> None:
        """Create DNS record in zone."""
        self._request('POST', self._rrset_url(zone_name, rrset_name, type_), data=data)

    def record_update(self, zone_name: str, rrset_name: str, type_: str, data: dict) -> None:
        """Update DNS record in zone."""
        self._request('PUT', self._rrset_url(zone_name, rrset_name, type_), data=data)

    def record_get(self, zone_name: str, rrset_name: str, type_: str) -> dict:
        """Get DNS record in zone."""
        return self._request('GET', self._rrset_url(zone_name, rrset_name, type_)).json()

    def record_content(self, zone_name: str, rrset_name: str, type_: str) -> typing.List[str]:
        """Get record content."""
        response = self.record_get(zone_name, rrset_name, type_)
        return [record['content'][0] for record in response['resource_records']]

    def record_delete(self, zone_name: str, rrset_name: str, type_: str) -> None:
        """Delete DNS record in zome."""
        self._request('DELETE', self._rrset_url(zone_name, rrset_name, type_))

    def _rrset_url(self, zone_name: str, rrset_name: str, type_: str) -> str:
        """Build full DNS URL for request."""
        return self._build_url(self._dns_api_url, self._root_zones, zone_name, rrset_name, type_)

    @staticmethod
    def _build_url(base: str, *items: typing.Iterable) -> typing.AnyStr:
        if not re.match(r'^https?://', base):
            raise GCoreException('Error schema url: please, check schema in url: "%s"' % base)
        for item in items:
            base = base.strip('/') + '/'
            base = urllib.parse.urljoin(base, item)
        return base
