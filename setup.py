from setuptools import find_packages
from setuptools import setup
from certbot_dns_gcore.__version__ import VERSION


install_requires = [
    'certbot>=1.23.0',
    'setuptools>=39.0.1',
]

docs_extras = [
    'Sphinx>=1.0',
    'sphinx_rtd_theme',
]

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='certbot-dns-gcore',
    version=VERSION,
    description="G-Core DNS Authenticator plugin for Certbot",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/G-Core/gcore-dns-certbot-plugin',
    author="G-Core Labs",
    author_email='support@gcorelabs.com',
    license='Apache License 2.0',
    python_requires='>=3.8',
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
