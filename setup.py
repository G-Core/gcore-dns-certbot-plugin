from setuptools import find_packages
from setuptools import setup

version = '0.1.0'

install_requires = [
    'certbot>=1.23.0',
    'setuptools>=39.0.1',
]

docs_extras = [
    'Sphinx>=1.0',
    'sphinx_rtd_theme',
]

setup(
    name='certbot-dns-gcore',
    version=version,
    description="G-Core DNS Authenticator plugin for Certbot",
    url='https://github.com/G-Core/terraform-provider-gcorelabs',
    author="G-Core Labs",
    author_email='support@gcorelabs.com',
    license='Apache License 2.0',
    python_requires='>=3.6',
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    extras_require={
        'docs': docs_extras,
    },
    entry_points={
        'certbot.plugins': [
            'dns-gcore = certbot_dns_gcore.dns_gcore:Authenticator',
        ],
    },
)
