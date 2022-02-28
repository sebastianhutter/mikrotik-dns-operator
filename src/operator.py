#!/usr/bin/env python3

import logging
import kopf
import os
from mikrotik import MikrotikClient, MikrotikClientException, MikrotikDnsEntryNotManaged


# parse configuration options
try:
    from dotenv import load_dotenv

    load_dotenv('.env', )
    load_dotenv('../.env')

    MIKROTIK_HOST = os.getenv('MIKROTIK_HOST')
    MIKROTIK_SSH_PORT = os.getenv('MIKROTIK_SSH_PORT', '22')
    MIKROTIK_SSH_HOST_KEY = os.getenv('MIKROTIK_SSH_HOST_KEY')
    MIKROTIK_SSH_USERNAME = os.getenv('MIKROTIK_SSH_USERNAME')
    MIKROTIK_SSH_PASSWORD = os.getenv('MIKROTIK_SSH_PASSWORD')
    MIKROTIK_SSH_PRIVATE_KEY = os.getenv('MIKROTIK_SSH_PRIVATE_KEY')
    MIKROTIK_SSH_PASSPHRASE = os.getenv('MIKROTIK_SSH_PASSPHRASE')
    MIKROTIK_DNS_ENTRY_ANNOTATION = os.getenv('MIKROTIK_DNS_ENTRY_COMMENT', 'tooling.hutter.cloud/mikrotik-static-ip')
    MIKROTIK_DNS_ENTRY_TTL = os.getenv('MIKROTIK_DNS_ENTRY_TTL', '5m')

    if not MIKROTIK_HOST:
        raise ValueError('MIKROTIK_HOST not set')
    if not MIKROTIK_SSH_HOST_KEY:
        raise ValueError('MIKROTIK_SSH_HOST_KEY not set')
    if not MIKROTIK_SSH_USERNAME:
        raise ValueError('MIKROTIK_SSH_USERNAME not set')
    if not MIKROTIK_SSH_PASSWORD and not MIKROTIK_SSH_PRIVATE_KEY:
        raise ValueError('MIKROTIK_SSH_PASSWORD and MIKROTIK_SSH_PRIVATE_KEY not set. Please specify at least one!')
except MikrotikClientException as e:
    raise e

try:
    # initialize mikrotik client
    MIKROTIK_CLIENT=MikrotikClient(
        host=MIKROTIK_HOST,
        port=MIKROTIK_SSH_PORT,
        host_key=MIKROTIK_SSH_HOST_KEY,
        username=MIKROTIK_SSH_USERNAME,
        password=MIKROTIK_SSH_PASSWORD,
        private_key=MIKROTIK_SSH_PRIVATE_KEY,
        passphrase=MIKROTIK_SSH_PASSPHRASE,
        comment=MIKROTIK_DNS_ENTRY_ANNOTATION,
        ttl=MIKROTIK_DNS_ENTRY_TTL,
    )
except MikrotikClientException as e:
    raise e

@kopf.on.startup()
def startup(settings: kopf.OperatorSettings, **kwargs):
    # fix suddenly stopping handlers. most certainly to do with aks backend connections
    # https://github.com/nolar/kopf/issues/585
    settings.watching.client_timeout = 600
    settings.watching.server_timeout = 600

@kopf.on.create(
    'networking.k8s.io',
    'v1',
    'ingresses',
    annotations={f'{MIKROTIK_DNS_ENTRY_ANNOTATION}': kopf.PRESENT}
)
@kopf.on.update(
    'networking.k8s.io',
    'v1',
    'ingresses',
    annotations={f'{MIKROTIK_DNS_ENTRY_ANNOTATION}': kopf.PRESENT}
)
def on_create_or_update_ingress(spec, meta, **kwargs):
    """
    create or update dns entries for ingresses having the mikrotik annotation

    :param spec:
    :param kwargs:
    :return:
    """

    address = meta.get('annotations').get(MIKROTIK_DNS_ENTRY_ANNOTATION)
    rules = spec.get('rules')
    try:
        for r in rules:
            MIKROTIK_CLIENT.upsert_static_dns_entry(
                address=address,
                name=r.get('host'),
            )
    except MikrotikClientException as e:
        kopf.TemporaryError(e)
    except MikrotikDnsEntryNotManaged as e:
        kopf.PermanentError(e)

@kopf.on.delete(
    'networking.k8s.io',
    'v1',
    'ingresses',
    annotations={f'{MIKROTIK_DNS_ENTRY_ANNOTATION}': kopf.PRESENT}
)
def on_delete_ingress(spec, **kwargs):
    """
    delete static dns entry when ingress resource is removed

    :param spec:
    :param kwargs:
    :return:
    """
    rules = spec.get('rules')
    try:
        for r in rules:
            MIKROTIK_CLIENT.delete_static_dns_entry(
                name=r.get('host'),
            )
    except MikrotikClientException as e:
        kopf.TemporaryError(e)
    except MikrotikDnsEntryNotManaged as e:
        kopf.PermanentError(e)

if __name__ == "__main__":
    logging.error("Started as script - please execute with `kopf run ./apim_registration_operator.py --all-namespaces --verbose")
