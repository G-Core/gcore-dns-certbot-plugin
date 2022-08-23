"""DNS Authenticator for G-Core."""

import logging
from typing import Any
from typing import Callable
from typing import Optional

from certbot import errors
from certbot.plugins import dns_common
from certbot.plugins.dns_common import CredentialsConfiguration

from . import api_gcore
from .api_gcore import GCoreConflictException

logger = logging.getLogger(__name__)


class Authenticator(dns_common.DNSAuthenticator):
    """DNS Authenticator for G-Core

    This Authenticator uses the G-Core DNS API to fulfill a dns-01 challenge.
    """

    _docs_url = 'https://apidocs.gcorelabs.com/dns#section/Authentication'
    description = ('Obtain certificates using a DNS TXT record (if you are using G-Core for '
                   'DNS).')
    ttl = 300

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.token = self.email = self.password = None
        self.credentials: Optional[CredentialsConfiguration] = None
        self.api_url = None
        self.auth_url = None
        self.dns_api_url = None

    @classmethod
    def add_parser_arguments(
            cls, add: Callable[..., None], default_propagation_seconds: int = 10
    ) -> None:
        super().add_parser_arguments(add, default_propagation_seconds)
        add('credentials', help='G-Core credentials INI file.')

    def more_info(self) -> str:
        return 'This plugin configures a DNS TXT record to respond to a dns-01 challenge using the G-Core API.'

    def _validate_credentials(self, credentials: CredentialsConfiguration) -> None:
        self.token = credentials.conf('apitoken')
        self.email = credentials.conf('email')
        self.password = credentials.conf('password')
        self.auth_url = credentials.conf('auth_url')
        self.dns_api_url = credentials.conf('dns_api_url')
        self.api_url = credentials.conf('api_url')

        if self.token:
            if self.email or self.password:
                raise errors.PluginError('{}: dns_gcore_email and dns_gcore_password are '
                                         'not needed when using an API Token'
                                         .format(credentials.confobj.filename))
        elif self.email or self.password:
            if not self.email:
                raise errors.PluginError('{}: dns_gcore_email is required when using a Global '
                                         'API Key. (should be email address associated with '
                                         'G-Core account)'.format(credentials.confobj.filename))
            if not self.password:
                raise errors.PluginError('{}: dns_gcore_password is required when using a '
                                         'Global API Key. (see {})'
                                         .format(credentials.confobj.filename, self._docs_url))
        else:
            raise errors.PluginError(
                '{}: Either dns_gcore_apitoken (recommended), or '
                'dns_gcore_email and dns_gcore_password are required.'
                ' (see {})'.format(credentials.confobj.filename, self._docs_url)
            )

    def _setup_credentials(self) -> None:
        self.credentials = self._configure_credentials(
            'credentials',
            'G-Core credentials INI file',
            None,
            self._validate_credentials
        )

    def _perform(self, domain: str, validation_name: str, validation: str) -> None:
        self._get_client().add_txt_record(domain, validation_name, validation, self.ttl)

    def _cleanup(self, domain: str, validation_name: str, validation: str) -> None:
        self._get_client().del_txt_record(domain, validation_name)

    def _get_client(self) -> "_GCoreClient":
        if not self.credentials:  # pragma: no cover
            raise errors.Error("Plugin has not been prepared.")
        if self.token:
            return _GCoreClient(
                token=self.token,
                api_url=self.api_url,
                dns_api_url=self.dns_api_url,
                auth_url=self.auth_url
            )
        return _GCoreClient(
            login=self.email,
            password=self.password,
            api_url=self.api_url,
            dns_api_url=self.dns_api_url,
            auth_url=self.auth_url
        )


class _GCoreClient:
    """
    G-Core client.
    """

    record_type = 'TXT'

    def __init__(self, *args, **kwargs) -> None:
        self.gcore = api_gcore.GCoreClient(*args, **kwargs)

    def add_txt_record(
            self, domain: str, record_name: str, record_content: str, record_ttl: int
    ) -> None:
        """
        Add a TXT record using the supplied information.

        :param str domain: The domain to use for verification.
        :param str record_name: The record name (typically beginning with '_acme-challenge.').
        :param str record_content: The record content (typically the challenge validation).
        :param int record_ttl: The record TTL (number of seconds that the record may be cached).
        :raises certbot.errors.PluginError: if an error occurs communicating with the G-Core DNS API
        """
        domain = self._find_zone_name(domain=domain)
        try:
            self.gcore.record_create(
                domain, record_name, self.record_type, data=self._data_for_txt(record_ttl, [record_content]),
            )
        except GCoreConflictException:
            logger.debug('Record already present on zone. Try to update record content')
            exist_record_content = self.gcore.record_content(domain, record_name, self.record_type)
            if record_content not in exist_record_content:
                exist_record_content.append(record_content)
            self.gcore.record_update(
                domain,
                record_name,
                self.record_type,
                data=self._data_for_txt(record_ttl, exist_record_content),
            )
        logger.debug('Successfully added TXT record with record_name: %s', record_name)

    def del_txt_record(self, domain: str, record_name: str) -> None:
        """
        Delete a TXT record using the supplied information.

        :param str domain: The domain to use for verification.
        :param str record_name: The record name (typically beginning with '_acme-challenge.').
        :param str record_content: The record content (typically the challenge validation).
        """
        try:
            domain = self._find_zone_name(domain)
            self.gcore.record_get(domain, record_name, self.record_type)
        except (api_gcore.GCoreNotFoundException, api_gcore.GCoreConflictException) as err:
            logger.debug('Encountered error finding zone_id during deletion: %s', err)
            return
        self.gcore.record_delete(domain, record_name, self.record_type)
        logger.debug('Successfully deleted TXT record.')

    @classmethod
    def _data_for_txt(cls, ttl, contents: list) -> dict:
        """Preparing data for TXT record."""
        return {'resource_records': [{'content': [content], 'enabled': True} for content in contents], 'ttl': ttl}

    def _find_zone_name(self, domain: str) -> str:
        """
        Find the zone_name for a given domain.

        Args:
            domain: The domain for which to find the zone_id.

        Returns:
            The zone_id, if found.
        """
        limit = 100
        domain_slit_list = '.'.join(domain.split('.')[-2:])
        zone_name_guesses = dns_common.base_domain_name_guesses(domain)[:-1]
        zones_raw = self.gcore.zones({'limit': limit, 'name': domain_slit_list})
        zones = [zona.get('name') for zona in zones_raw]

        for zone_name in zone_name_guesses:
            if zone_name in zones:
                logger.debug('Found zone_name: %s for domain: %s', zone_name, domain)
                return zone_name
        raise errors.PluginError(
            'Unable to determine zone name for {0} using zone names: '
            '{1}. Please confirm that the domain name has been '
            'entered correctly and is already associated with the '
            'supplied G-Core account.'.format(domain, zone_name_guesses)
        )
