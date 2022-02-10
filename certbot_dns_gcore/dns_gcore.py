"""DNS Authenticator for G-Core."""

import logging
from typing import Any
from typing import Callable
from typing import Optional

from certbot import errors
from certbot.plugins import dns_common
from certbot.plugins.dns_common import CredentialsConfiguration

from . import api_gcore

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

    @classmethod
    def add_parser_arguments(
            cls, add: Callable[..., None], default_propagation_seconds: int = 10
    ) -> None:
        super().add_parser_arguments(add, default_propagation_seconds)
        add('credentials', help='G-Core credentials INI file.')

    def more_info(self) -> str:
        return 'This plugin configures a DNS TXT record to respond to a dns-01 challenge using ' + \
               'the G-Core API.'

    def _validate_credentials(self, credentials: CredentialsConfiguration) -> None:
        self.token = credentials.conf('apitoken')
        self.email = credentials.conf('email')
        self.password = credentials.conf('password')
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
            return _GCoreClient(token=self.token)
        return _GCoreClient(login=self.email, password=self.password)


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
        self.gcore.record_create(
            domain,
            record_name,
            self.record_type,
            data=self._data_for_txt(record_ttl, record_content),
        )
        logger.debug('Successfully added TXT record with record_name: %s', record_name)

    def del_txt_record(self, domain: str, record_name: str) -> None:
        """
        Delete a TXT record using the supplied information.

        :param str domain: The domain to use for verification.
        :param str record_name: The record name (typically beginning with '_acme-challenge.').
        :param str record_content: The record content (typically the challenge validation).
        """
        self.gcore.record_delete(domain, record_name, self.record_type)
        logger.debug('Successfully deleted TXT record.')

    @classmethod
    def _data_for_txt(cls, _ttl, _content):
        """Preparing data for TXT record."""
        return {'resource_records': [{'content': [_content], 'enabled': True}], 'ttl': _ttl}
