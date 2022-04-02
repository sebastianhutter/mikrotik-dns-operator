import pytest
from . import Config
import os

class TestConfig(object):
    def _setup_complete_environment(self):
        os.environ['MIKROTIK_HOST'] = '127.0.0.1'
        os.environ['MIKROTIK_SSH_HOST_KEY'] = 'ssh-rsa'
        os.environ['MIKROTIK_SSH_USERNAME'] = 'username'
        os.environ['MIKROTIK_SSH_PASSWORD'] = 'password'
        os.environ['MIKROTIK_SSH_PRIVATE_KEY'] = 'ssh-rsa'
        os.environ['MIKROTIK_SSH_PASSPHRASE'] = 'passphrase'

    def _test_configuration_value(self, env, exception):
        self._setup_complete_environment()

        for e in env:
            os.environ.pop(e)
        with pytest.raises(ValueError, match=exception):
            c = Config(load_dotenv=False)


    def test_succeed_with_valid_environment(self):
        self._setup_complete_environment()
        c = Config(load_dotenv=False)

        assert c.mikrotik_host == '127.0.0.1'
        assert c.mikrotik_ssh_port == '22'
        assert c.mikrotik_ssh_host_key == 'ssh-rsa'
        assert c.mikrotik_ssh_username == 'username'
        assert c.mikrotik_ssh_password == 'password'
        assert c.mikrotik_ssh_private_key == 'ssh-rsa'
        assert c.mikrotik_ssh_passphrase == 'passphrase'
        assert c.mikrotik_dns_entry_comment == 'tooling.hutter.cloud/mikrotik-static-ip'
        assert c.mikrotik_k8s_annotation == 'tooling.hutter.cloud/mikrotik-static-ip'
        assert c.mikrotik_dns_entry_ttl == '5m'

    def test_fail_with_empty_mikrotik_host(self):
        self._test_configuration_value(['MIKROTIK_HOST'], 'MIKROTIK_HOST not set')

    def test_fail_with_empty_mikrotik_ssh_host_key(self):
        self._test_configuration_value(['MIKROTIK_SSH_HOST_KEY'], 'MIKROTIK_SSH_HOST_KEY not set')

    def test_fail_with_empty_mikrotik_ssh_username(self):
        self._test_configuration_value(['MIKROTIK_SSH_USERNAME'], 'MIKROTIK_SSH_USERNAME not set')

    def test_fail_with_empty_mikrotik_ssh_password_and_private_key(self):
        self._test_configuration_value(
            ['MIKROTIK_SSH_PASSWORD', 'MIKROTIK_SSH_PRIVATE_KEY'],
            'MIKROTIK_SSH_PASSWORD and MIKROTIK_SSH_PRIVATE_KEY not set. Please specify at least one!'
        )