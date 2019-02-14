# ldap-auth
NSO LDAP External Authentication example

##### NSO Configuration updates to ncs.conf
```
<external-authentication>
    <enabled>true</enabled>
    <executable>path/to/ldap-auth.py</executable>
</external-authentication>
```

##### NSO External Authentication Architecture
![architecture](img/external_auth_architecture.jpg)

##### External Authentication Script Input/Output
Standard Input
* [username;password]

Standard Output:
* accept $groups $uid $gid $supplementary_gids $HOME
* reject Message
* abort Message
* Will not proceed with other authentication methods specified.

##### Accept Attributes
• $groups - space separated list of the group names the user is a member of.
• $uid - UNIX integer user id NSO should use as default when executing commands for this user.
• $gid - UNIX integer group id NSO should use as default when executing commands for this user.
• $supplementary_gids - (possibly empty) space separated list of additional UNIX group ids the user is also
a member of.

#### Contact

Contact Hakan Niska <hniska@cisco.com> with any suggestions or comments. If you find any bugs please fix them and send me a pull request.
