#### NSO LDAP External Authentication Architecture
![architecture](img/external_auth_architecture.jpg)

To interface with an external authentication entity, e.g. RADIUS or LDAP server,
the user needs to provide an authentication script/program that will interact with the specific authentication method.
The purpose of the script is to not only solicit the remote authentication server for user/password acceptance
but also to determine the groups that are associated with the user.
These groups are then returned from the script to NCS, prepended to any group information stored locally under the
_/aaa_ tree, and used by the NCS authorization process when checking rules.

The authentication server of choice must be configured for each user to return accept/reject result and provide user
and group identifiers in a format that is expected by the authentication script being provided.

#### External Authentication Script Input/Output
Standard input
* [username;password]

Standard output:
* accept $groups $uid $gid $supplementary_gids $HOME
    * $groups - space separated list of the group names the user is a member of.
    * $uid - UNIX integer user id NSO should use as default when executing commands for this user.
    * $gid - UNIX integer group id NSO should use as default when executing commands for this user.
    * $supplementary_gids - (possibly empty) space separated list of additional UNIX group ids the user is also a member of.
* reject message
* abort message
  * Will not proceed with other authentication methods specified.

#### Prerequisite

Need install Python package _python-ldap_:
```
pip install python-ldap
```

#### NSO Configuration

NCS base configuration in _ncs.conf_ must include an _<external-authentication>_ clause with the _<aaa>_
configuration to enable external authentication and provide the location of the authentication executable:
```
<aaa>
    <external-authentication>
        <enabled>true</enabled>
        <executable>./scripts/python/ldap-auth.py</executable>
    </external-authentication>
</aaa>
```

##### Test

```
bash$> ./ldap-auth.py
[bob;is-the-king;]
accept "Administrators" "Sweden North" "Elvis is alive" 501 20 12 /tmp

bash$> ./ldap-auth.py
[bob;didntwin;]
reject ERROR:root:could not connect to AD server
```
#### Contact

Contact Hakan Niska <hniska@cisco.com> with any suggestions or comments. If you find any bugs please fix them and send me a pull request.
