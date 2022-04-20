"""Wrapper for G-Core DNS API."""

import http
import logging
import urllib.parse

from requests import Session

logger = logging.getLogger(__name__)


class GCoreClientException(Exception):
    """G-Core DNS API client exception."""


class GCoreClient:
    """G-Core DNS API client."""

    _root_zones = 'zones'
    _dns_api_url = 'https://api.gcorelabs.com/dns/v2/'
    _auth_url = 'https://api.gcdn.co/'

    def __init__(self, token=None, login=None, password=None):
        self._session = Session()
        if token is not None:
            self._session.headers.update({'Authorization': f'APIKey {token}'})
        elif login is not None and password is not None:
            token = self._auth(self._auth_url, login, password)
            self._session.headers.update({'Authorization': f'Bearer {token}'})
        else:
            raise ValueError('either token or login & password must be set')

    def _auth(self, url, login, password):
        """Get auth token."""
        responce = self._session.request(
            'POST',
            self._build_url(url, 'auth', 'jwt', 'login'),
            json={'username': login, 'password': password},
        )
        responce.raise_for_status()
        return responce.json()['access']

    def _request(self, method, url, params=None, data=None):
        """Requests handler."""
        responce = self._session.request(method, url, params=params, json=data, timeout=30.0)
        if responce.status_code in (
            http.HTTPStatus.BAD_REQUEST,
            http.HTTPStatus.NOT_FOUND,
            http.HTTPStatus.INTERNAL_SERVER_ERROR,
            http.HTTPStatus.CONFLICT,
        ):
            logger.error(
                'Something went wrong. %r has been sent to %r: %s', data, url, responce.text,
            )
            raise GCoreClientException(responce.text)
        responce.raise_for_status()
        return responce

    def zone(self, zone_name):
        """Get DNS record."""
        return self._request(
            'GET', self._build_url(self._dns_api_url, self._root_zones, zone_name)
        ).json()

    def zone_create(self, zone_name):
        """Create DNS zone."""
        return self._request(
            'POST',
            self._build_url(self._dns_api_url, self._root_zones),
            data={'name': zone_name},
        ).json()

    def zone_records(self, zone_name):
        """List DNS records from zone."""
        url = self._build_url(self._dns_api_url, self._root_zones, zone_name, 'rrsets')
        rrsets = self._request('GET', url, params={'all': 'true'}).json()
        records = rrsets['rrsets']
        return records

    def record_create(self, zone_name, rrset_name, type_, data):
        """Create DNS record in zone."""
        self._request('POST', self._rrset_url(zone_name, rrset_name, type_), data=data)

    def record_update(self, zone_name, rrset_name, type_, data):
        """Update DNS record in zone."""
        self._request('PUT', self._rrset_url(zone_name, rrset_name, type_), data=data)

    def record_delete(self, zone_name, rrset_name, type_):
        """Delete DNS record in zome."""
        self._request('DELETE', self._rrset_url(zone_name, rrset_name, type_))

    def _rrset_url(self, zone_name, rrset_name, type_):
        """Build full DNS URL for request."""
        return self._build_url(self._dns_api_url, self._root_zones, zone_name, rrset_name, type_)

    @staticmethod
    def _build_url(base, *items):
        for i in items:
            base = base.strip('/') + '/'
            base = urllib.parse.urljoin(base, i)
        return base
