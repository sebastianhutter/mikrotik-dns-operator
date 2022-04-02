from dotenv import load_dotenv
import os

class Config(object):
    """
        simple configuration class
    """

    def __init__(self):
        """
            initialize the operator configuration from environment variables
        """

        load_dotenv('.env', )
        load_dotenv('../.env')

        self.mikrotik_host = os.getenv('MIKROTIK_HOST')
        self.mikrotik_ssh_port = os.getenv('MIKROTIK_SSH_PORT', '22')
        self.mikrotik_ssh_host_key = os.getenv('MIKROTIK_SSH_HOST_KEY')
        self.mikrotik_ssh_username = os.getenv('MIKROTIK_SSH_USERNAME')
        self.mikrotik_ssh_password = os.getenv('MIKROTIK_SSH_PASSWORD')
        self.mikrotik_ssh_private_key = os.getenv('MIKROTIK_SSH_PRIVATE_KEY')
        self.mikrotik_ssh_passphrase = os.getenv('MIKROTIK_SSH_PASSPHRASE')
        self.mikrotik_dns_entry_comment = os.getenv('MIKROTIK_DNS_ENTRY_COMMENT', 'tooling.hutter.cloud/mikrotik-static-ip')
        self.mikrotik_k8s_annotation = os.getenv('MIKROTIK_K8S_ANNOTATION', 'tooling.hutter.cloud/mikrotik-static-ip')
        self.mikrotik_dns_entry_ttl = os.getenv('MIKROTIK_DNS_ENTRY_TTL', '5m')

        if not self.mikrotik_host:
            raise ValueError('MIKROTIK_HOST not set')
        if not self.mikrotik_ssh_host_key:
            raise ValueError('MIKROTIK_SSH_HOST_KEY not set')
        if not self.mikrotik_ssh_username:
            raise ValueError('MIKROTIK_SSH_USERNAME not set')
        if not self.mikrotik_ssh_password and not self.mikrotik_ssh_private_key:
            raise ValueError('MIKROTIK_SSH_PASSWORD and MIKROTIK_SSH_PRIVATE_KEY not set. Please specify at least one!')