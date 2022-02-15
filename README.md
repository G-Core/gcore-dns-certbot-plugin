The `certbot_dns_gcore` plugin automates the process of
completing a `dns-01` challenge (`acme.challenges.DNS01`) by
creating, and subsequently removing, TXT records using the G-Core DNS
API.

Documentation
===============
For full documentation, including installation, examples, changelog please see [readthedocs page](https://gcore-dns-certbot-plugin.readthedocs.io/en/latest/).

Install
===============

The plugin is not installed by default. It can be installed by command
below.

``` {.bash}
pip install certbot-dns-gcore
```

Named Arguments
===============

| plugin flags | Description |
| ----------- | ----------- |
| `--dns-gcore-credentials` | G-Core credentials INI file. (Required) |
| `--dns-gcore-propagation-seconds` | The number of seconds to wait for DNS to propagate before asking the ACME server to verify the DNS record. (Default: 10) |


Credentials
===========

Use of this plugin requires a configuration file containing G-Core DNS
API credentials. You can use:
* G-Core API Token, obtained from your [profile panel](https://accounts.gcorelabs.com/profile/api-tokens) 
or
* use G-Core Authentication credentials (email and password) for [login](https://auth.gcorelabs.com/login/signin) page.

G-Core API Token is **recommended** authentication option.

The token needed by Certbot for add temporary TXT record to zone what
you need certificates for.

Example `gcore.ini` credentials file using restricted API Token (recommended)
```ini
# G-Core API token used by Certbot
dns_gcore_apitoken = 0123456789abcdef0123456789abcdef01234567
```
Example `gcore.ini` credentials file using authentication credentials (not recommended)
```ini
# G-Core API credentials used by Certbot
dns_gcore_email = gcore_user@example.com
dns_gcore_password = 0123456789abcdef0123456789abcdef01234
```

The path to this file can be provided interactively or using the
`--dns-gcore-credentials` command-line argument. Certbot records the
path to this file for use during renewal, but does not store the file\'s
contents.

> **WARNING**:
You should protect these API credentials as you would the password to
your G-Core account. Users who can read this file can use these
credentials to issue arbitrary API calls on your behalf. Users who can
cause Certbot to run using these credentials can complete a `dns-01`
challenge to acquire new certificates or revoke existing certificates
for associated domains, even if those domains aren\'t being managed by
this server.

Certbot will emit a warning if it detects that the credentials file can
be accessed by other users on your system. The warning reads \"Unsafe
permissions on credentials configuration file\", followed by the path to
the credentials file. This warning will be emitted each time Certbot
uses the credentials file, including for renewal, and cannot be silenced
except by addressing the issue (e.g., by using a command like
`chmod 600` to restrict access to the file).

Examples
========
To acquire a certificate for ``example.com``
```bash
certbot certonly --authenticator dns-gcore --dns-gcore-credentials=./gcore.ini -d 'example.com'
```

To acquire a certificate for ``example.com``, waiting 60 seconds for DNS propagation
```bash
certbot certonly --authenticator dns-gcore --dns-gcore-credentials=./gcore.ini --dns-gcore-propagation-seconds=60 -d 'example.com'
```

For developers
========

How to run\develop plugin in docker
```bash
docker-compose run --rm --service-ports dev bash
# commands below run inside docker container
pip install -e .
touch ./gcore.ini # add g-core dns api credentials
certbot certonly --authenticator dns-gcore --dns-gcore-credentials=./gcore.ini -d 'example.com'
```

Main docs file here: `certbot_dns_gcore/__init__.py`

How to run tests:
please see document `.github/workflows/ci.yml`
