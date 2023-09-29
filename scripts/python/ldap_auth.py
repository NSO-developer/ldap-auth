#!/usr/bin/env python
import os
import logging
import sys

import ldap
import ncs
import _ncs

# Setup logger
logdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "/var/log/ncs")
logname = os.path.join(logdir, "ncs-python-ldap-auth.log")
if not os.path.isdir(logdir):
    os.mkdir(logdir)

logging.basicConfig(filename=logname,
                    filemode='a+',
                    format='%(asctime)s.%(msecs)02d %(filename)s:%(lineno)s %(levelname)s: %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)


class LdapConfig(object):
    def __init__(self, server, admin, pswd, bdn, prefix, group):
        self.server_url = server
        self.admin_user = admin
        self.admin_pswd = pswd
        self.base_dn = bdn
        self.user_dn_prefix = prefix
        self.user_dn_group = group


def get_ldap_config_details():
    """Retrieve the ldap host and secret stored within NSO"""

    # Create NCS connection to read ldap host details
    logger.info("Connecting to NSO to retrieve ldap configuration details")
    with ncs.maapi.Maapi() as m:
        with ncs.maapi.Session(m, 'admin', 'system'):
            with m.start_read_trans() as trans:
                m.install_crypto_keys()
                root = ncs.maagic.get_root(trans)

                # ldap Server Details
                server = root.ldap.server
                admin = root.ldap.login.username
                secret = root.ldap.login.password
                pswd = _ncs.decrypt(secret)
                base_dn = root.ldap.base_dn
                dn_prefix = root.ldap.user_dn_prefix
                dn_group = root.ldap.user_dn_group

    logging.debug(f'ldap server: {server}')
    logging.debug(f'ldap base_dn: {base_dn}')
    logging.debug(f'ldap dn_prefix: {dn_prefix}')
    logging.debug(f'ldap dn_group: {dn_group}')
    logging.debug(f'ldap admin user: {admin}')
    logging.debug(f'ldap admin password: {secret}')

    if not server or not pswd or not admin or not base_dn or not dn_group or not dn_prefix:
        error_message = "Error: Configuration for LDAP server access is incomplete"
        logger.error(error_message)
        print(error_message)
        exit(1)

    lc = LdapConfig(
        server,
        admin,
        pswd,
        base_dn,
        dn_prefix,
        dn_group,
    )
    return lc


def check_credentials(lc, user, user_password):

    user_dn = f'{lc.user_dn_prefix}={user},{lc.user_dn_group},{lc.base_dn}'

    ldap_admin_dn = f'{lc.admin_user}'
    ldap_filter = f'(&({lc.user_dn_prefix}={user}))'
    ldap_attrs = ['memberOf', 'gidNumber', 'uidNumber']
    logging.debug(f'ldap admin dn: {ldap_admin_dn}')
    logging.debug(f'user_dn: {user_dn}')
    logging.debug(f'ldap_filter: {ldap_filter}')
    logging.debug(f'search attributes: {ldap_attrs}')
    try:
        # create ldap client
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        ldap_client = ldap.initialize(lc.server_url)
    except ldap.SERVER_DOWN as err:
        logging.error('LDAP Exception SERVER DOWN:\n' + str(err))
        return 'reject Could not connect to LDAP server'

    try:
        ldap_client.set_option(ldap.OPT_REFERRALS, 0)
        ldap_client.simple_bind_s(ldap_admin_dn, lc.admin_pswd)
    except ldap.INVALID_CREDENTIALS as err:
        ldap_client.unbind()
        logging.error('LDAP Exception INVALID_CREDENTIALS:\n' + str(err))
        return f'reject Wrong LDAP admin dn ({ldap_admin_dn}) or password'
    except Exception as err:
        ldap_client.unbind()
        logging.error('Exception while binding to the LDAP server:\n' + str(err))
        return 'reject Exception while binding to LDAP server: ' + str(err)

    # get all user attributes defined in ldap_attrs
    try:
        results = ldap_client.search_s(lc.base_dn, ldap.SCOPE_SUBTREE, ldap_filter, ldap_attrs)
        ldap_client.unbind()
    except ldap.NO_SUCH_OBJECT as err:
        ldap_client.unbind()
        logging.error(f'Exception while searching the user {user}:\n' + str(err))
        return 'reject Exception while binding to LDAP server: ' + str(err)

    if not results:
        return f"reject Wrong user dn ({user_dn})"
    user_attrs = results[0][1]
    # Verify username and password is valid
    logging.error(str(results[0][0]))
    if user_password == "":
        return "reject Empty password"
    try:
        ldap_client_user = ldap.initialize(lc.server_url)
        ldap_client_user.set_option(ldap.OPT_REFERRALS, 0)
        ldap_client_user.simple_bind_s(str(results[0][0]), user_password)
    except ldap.INVALID_CREDENTIALS as err:
        ldap_client_user.unbind()
        logging.error('LDAP Exception INVALID_CREDENTIALS:\n' + str(err))
        return f'reject LDAP username or password wrong'
    except Exception as err:
        ldap_client_user.unbind()
        logging.error('Exception while binding to the LDAP server:\n' + str(err))
        return 'reject Exception while binding to LDAP server: ' + str(err)

    if 'memberOf' in user_attrs:
        user_groups = user_attrs['memberOf']
        group_list = []
        for group in user_groups:
            group_list.append(str(group).split(",")[0].split("=")[1])

        # response to NSO with accept and the list of group membership.
        return f"accept {' '.join(group_list)} 65534 65534 65534 $HOME"
    else:
        return f'reject User {user} is not a member of any group'


def parse_credentials(credential_string):
    """
    Parse username and password input received from NSO as part of external authentication.
    Expected format: [username;password;]
    """
    credentials_list = credential_string[1:].split(";")
    username = credentials_list[0]
    password = credentials_list[1]
    return username, password


if __name__ == "__main__":
    # Retrieve LDAP configuration from NSO CDB
    ldap_config = get_ldap_config_details()

    # Read user credentials passed from NSO
    credentials = sys.stdin.readline()
    username, password = parse_credentials(credentials)  # 'yanlab', 'cisco123'
    logger.info(f"Requested authenticate user with: username={username}, password=********")

    response = check_credentials(ldap_config, username, password)

    logger.info(f"Exiting with response: {response}")
    print(response)
