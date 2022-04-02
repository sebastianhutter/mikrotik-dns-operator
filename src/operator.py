#!/usr/bin/env python3

import logging
import kopf
import os
from mikrotik import MikrotikClient, MikrotikClientException, MikrotikDnsEntryNotManaged
from configuration import Config

# parse configuration options
try:
    c = Config()
except ValueError as e:
    raise e

try:
    # initialize mikrotik client
    MIKROTIK_CLIENT=MikrotikClient(
        host=c.mikrotik_host,
        port=c.mikrotik_ssh_port,
        host_key=c.mikrotik_ssh_host_key,
        username=c.mikrotik_ssh_username,
        password=c.mikrotik_ssh_password,
        private_key=c.mikrotik_ssh_private_key,
        passphrase=c.mikrotik_ssh_passphrase,
        comment=c.mikrotik_dns_entry_comment,
        ttl=c.mikrotik_dns_entry_ttl,
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
    annotations={f'{c.mikrotik_k8s_annotation}': kopf.PRESENT}
)
@kopf.on.update(
    'networking.k8s.io',
    'v1',
    'ingresses',
    annotations={f'{c.mikrotik_k8s_annotation}': kopf.PRESENT}
)
def on_create_or_update_ingress(spec, meta, **kwargs):
    """
    create or update dns entries for ingresses having the mikrotik annotation

    :param spec:
    :param kwargs:
    :return:
    """

    address = meta.get('annotations').get(c.mikrotik_k8s_annotation)
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
    annotations={f'{c.mikrotik_k8s_annotation}': kopf.PRESENT}
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
