#!/usr/local/bin/python
import ldap
import logging
import sys
from sys import stdin
#Change to level=logging.DEBUG for more verbose logging
logging.basicConfig(stream=sys.stderr, level=logging.ERROR)

def check_credentials(username, password):
    ldap_server = 'ldap://ds.example.com'
    ldap_username = '%s@example.com' % username
    ldap_password = password
    base_dn = 'DC=example,DC=com'
    ldap_filter = 'userPrincipalName=%s@example.com' % username
    group_attr = 'memberOf'
    logging.debug('ldap server: ' + ldap_server)
    logging.debug('ldap_username: ' + ldap_username)
    logging.debug('ldap_password: **********')
    logging.debug('base_dn: ' + base_dn)
    logging.debug('ldap_filter: ' + ldap_filter)
    logging.debug('group_attr: ' + group_attr)
    try:
        # build a client
        ldapClient = ldap.initialize(ldap_server)
        # perform a synchronous bind
        ldapClient.set_option(ldap.OPT_REFERRALS, 0)
        ldapClient.simple_bind_s(ldap_username, ldap_password)
    except ldap.INVALID_CREDENTIALS:
        ldapClient.unbind()
        print 'reject ', 'Wrong username or password'
    except ldap.SERVER_DOWN as e:
        print 'reject ' + 'Could not connect to LDAP server' + str(e)
    except Exception as e:
        logging.error('exception: ' + str(e))
        print 'reject ' + 'ERROR: ' + str(e)
    # all is well

    if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
        #List everything under the base DN.
        for name, attrs in ldapClient.search_s(base_dn, ldap.SCOPE_ONELEVEL, "objectclass=*", []):
            logging.debug('List base dn: ' + str(name))
    logging.debug('User objects: ' + str(ldapClient.search_s(base_dn, ldap.SCOPE_SUBTREE, ldap_filter)[0][1].keys()))

    # get all user groups and store it in groupList
    groups = ldapClient.search_s(base_dn, ldap.SCOPE_SUBTREE, ldap_filter, group_attr.split())[0][1][group_attr]
    ldapClient.unbind()
    groupList = []

    #add all groups in to a list
    #NSO cant handle groups with only numbers in it so remove those.
    for group in groups:
        if not group.split(",")[0].split("=")[1].isdigit():
            groupList.append('"' + group.split(",")[0].split("=")[1] + '"')

    #create one string out of that list.
    groupList = sorted(set(groupList))
    ' ,'.join(groupList)
    groupString = str(groupList).strip('[]').replace("'", "",).replace(",", "")
    #respond to NSO with accept and the list of group membership.
    print "accept", groupString, "501 20 12 /tmp\n"
    return None


def get_credentials():
    #read username and password from stdin
    #comes in [username;password;]\n format
    #just reading form stdin does not work for some reason.
    #might be that NSO does not send line break?
    #c = stdin.read()
    c = ""
    b = ""
    while True:
        try:
            a = stdin.read(1)
            c += a
            #would like to use something like this instead
            #($username, $password) = (<> =~ /^\[(.+?);(.+);\]$/);
            if a == ']':# and b == 'n':
              break
              b = a
        except (EOFError):
            break
    logging.debug('input string: ' + c)
    #Remove [ and ], split on ; and assign to username and password
    username = c.replace("\\n", "").strip('"[]').split(";")[0]
    password = c.replace("\\n", "").strip('"[]').split(";")[1]

    return (username, password)

"""
For testing purpouses run
#> python adauth.py
and then type
[username;password;]
"""
usernamePassword = get_credentials()
check_credentials(usernamePassword[0], usernamePassword[1])
