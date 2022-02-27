import logging
import tempfile

from paramiko import SSHClient, RSAKey, SSHException
from paramiko.py3compat import decodebytes
import base64
import re


class MikrotikClientException(Exception):
    def __init__(self, message):
        self.message = message

class MikrotikDnsEntryNotManaged(Exception):
    def __init__(self, name, address):
        self.message = f'Static dns entry with name {name} and address {address} found but not managed by operator'

class MikrotikStaticDnsEntry(object):
    def __init__(self, id, address, name, comment, ttl):
        self.id = id
        self.address = address
        self.name = name
        self.comment = comment
        self.ttl = ttl

class MikrotikClient(object):

    def __init__(self, host, port, host_key, username, password, private_key, passphrase, comment, ttl):
        """
        initialize the mikrotik ssh client.

        :param host:
        :param port:
        :param host_key:
        :param username:
        :param password:
        :param private_key:
        :param passphrase:
        """

        self.host = host
        self.port = port
        self.host_key = host_key
        self.username = username
        self.password = password
        self.passphrase = passphrase
        self.comment = comment
        self.ttl = ttl

        # try to decode the given private key
        self.private_key = None
        if private_key:
            try:
                self.base64_encoded_private_key = private_key
                pkey = tempfile.NamedTemporaryFile()
                pkey.write(base64.b64decode(self.base64_encoded_private_key))
                pkey.flush()
                self.private_key = RSAKey.from_private_key_file(filename=pkey.name, password=self.passphrase)
                self.pk = pkey.name
                pkey.close()
            except BaseException as e:
                raise MikrotikClientException(message=e)

        # setup client with host key
        try:
            self.client = SSHClient()
            # https://stackoverflow.com/questions/39523216/paramiko-add-host-key-to-known-hosts-permanently
            keyObj = RSAKey(data=decodebytes(self.host_key.encode()))
            self.client.get_host_keys().add(hostname=f'[{self.host}]:{self.port}', keytype="ssh-rsa", key=keyObj)
        except BaseException as e:
            raise MikrotikClientException(message=e)

    def cli(self, cli):
        """

        :param cli: the command to execute on the mikrotik router
        :return: output of command as list
        """

        logging.debug(f'Execute command on {self.host}: {cli}')
        try:
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                pkey=self.private_key,
                allow_agent=False,
                look_for_keys=False,
                # disable strong pub keys algorithms for mikrotik pkey authentication
                disabled_algorithms={'pubkeys': ['rsa-sha2-512', 'rsa-sha2-256']}
            )

            _, stdout, _ = self.client.exec_command(cli)
            retcode = stdout.channel.recv_exit_status()
            # if stderr or exit status raise an exception
            if retcode != 0:
                self.client.close()
                raise MikrotikClientException(f'SSH command "{cli}" returned invalid exit code {retcode}')

            retval = stdout.read().decode("utf8")
            # parse output for potential error messages
            if 'bad command' in retval:
                raise MikrotikClientException(retval)
            if 'invalid value for argument' in retval:
                raise MikrotikClientException(retval)

            retlines = []
            for l in retval.split('\r\n'):
                if not l.startswith('#') and len(l) > 0:
                    retlines.append(l)
            return retlines

        except SSHException as e:
            raise e
        finally:
            self.client.close()

    def get_static_dns_entries(self):
        """
        return all static dns entries
        :return: list of static dns entries
        """

        dns_entries_raw = self.cli('/ip dns static print terse')
        dns_entries_parsed = []
        for d in dns_entries_raw:
            entry = re.search(r'^\s?(?P<id>\d{1,2})\s+(comment=(?P<comment>.*?) )?name=(?P<name>.*?) address=(?P<address>.*?) ttl=(?P<ttl>.*?)$', d)
            if entry:
                dns_entries_parsed.append(
                    MikrotikStaticDnsEntry(
                        id=entry.group('id'),
                        address=entry.group('address'),
                        name=entry.group('name'),
                        comment=entry.group('comment'),
                        ttl=entry.group('ttl')
                    )
                )


        return dns_entries_parsed

    def upsert_dns_entry(self, address, name):
        """
        create or update a static dns entry
        :param address: the ip address for the dns entry
        :param name: the name of the dns entry
        :return: None
        """

        # first get a list of all dns entries
        static_dns_entries = self.get_static_dns_entries()

        # check if the given name already exists
        for d in static_dns_entries:
            if d.name == name and d.address != address and d.ttl != self.ttl:
                if d.comment != self.comment:
                    raise MikrotikDnsEntryNotManaged(address=d.address, name=d.name)

                logging.debug(f'Update dns entry {name} with address {address}')
                self.cli(f'/ip dns static set {d.id} address={address} ttl={self.ttl}')
                return

        # if dns enty wasnt found lets create it
        logging.debug(f'Create dns entry {name} with address {address}')
        self.cli(f'/ip dns static add name={name} address={address} comment={self.comment} ttl={self.ttl}')