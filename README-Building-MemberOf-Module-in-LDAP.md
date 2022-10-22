
## Building MemberOf Module in LDAP
There's no native application or shell in which you can fiddle. Instead, _openldap_ comes with a few executables
that you can use to perform your actions. You feed these executables with files containing the data you want to add.

### Adding organizational units
We need create two organizational unit nodes:
  - Node groups to include member groups associated with NSO
  - Node people to include all the users

Make a file named _add_nodes.ldif_ in your favorite text editor and add the following lines considering that our base is:
dc=example,dc=com:
```
dn: ou=people,dc=example,dc=com
objectClass: organizationalUnit
ou: people

dn: ou=groups,dc=example,dc=com
objectClass: organizationalUnit
ou: groups
```

To add these nodes, simply run the following command and give the admin password, that you chose during slapd setup,
when prompted:
```
ldapadd -x -D cn=admin,dc=example,dc=com -W -f add_nodes.ldif
```

### Enabling memberOf module
In order to easily and efficiently do query that enables you to see, which users are part of which groups,
we need to set up the feature in LDAP that allows us to do this. Make the following 3 files (based on
[this](https://blog.adimian.com/2014/10/15/how-to-enable-memberof-using-openldap/) publication):

**memberof_config.ldif**
```
dn: cn=module{1},cn=config
cn: module{1}
objectClass: olcModuleList
olcModuleLoad: memberof
olcModulePath: /usr/lib/ldap

dn: olcOverlay={0}memberof,olcDatabase={1}mdb,cn=config
objectClass: olcConfig
objectClass: olcMemberOf
objectClass: olcOverlayConfig
objectClass: top
olcOverlay: memberof
olcMemberOfDangling: ignore
olcMemberOfRefInt: TRUE
olcMemberOfGroupOC: groupOfNames
olcMemberOfMemberAD: member
olcMemberOfMemberOfAD: memberOf
```

**refint1.ldif**
```
dn: cn=module{1},cn=config
add: olcmoduleload
olcmoduleload: refint
```

**refint2.ldif**
```
dn: olcOverlay={1}refint,olcDatabase={1}mdb,cn=config
objectClass: olcConfig
objectClass: olcOverlayConfig
objectClass: olcRefintConfig
objectClass: top
olcOverlay: {1}refint
olcRefintAttribute: memberof member manager owner
```

To set up the _memberof_ module and configure it, run this command:
```
sudo ldapadd -Q -Y EXTERNAL -H ldapi:/// -f memberof_config.ldif
```

To load and configure the _refint_ module:
```
sudo ldapmodify -Q -Y EXTERNAL -H ldapi:/// -f refint1.ldif
sudo ldapadd -Q -Y EXTERNAL -H ldapi:/// -f refint2.ldif
```

> **Note!** Every _memberof_ related group created before this module is enabled must be deleted and remade for these
changes to take effect. LDAP assigns a "member" attribute behind the scenes to existing users when creating a group.

### Adding a user
Before we add new user, we need to generate its password hash:
```
slappasswd -h {SHA} -s my_secret_password
yielding this result:
{SHA}M6XDJwA47cNw9gm5kXV1uTQuMoY=
```

We will use this result when creating user file _add_user.ldif_:
```
dn: uid=ygorelik,ou=people,dc=example,dc=com
cn: Yan
sn: Gorelik
uid: ygorelik
uidNumber: 5000
gidNumber: 10000
homeDirectory: /home/john
mail: john.doe@example.com
objectClass: top
objectClass: posixAccount
objectClass: shadowAccount
objectClass: inetOrgPerson
objectClass: organizationalPerson
objectClass: person
loginShell: /usr/bin/bash
userPassword: {SHA}M6XDJwA47cNw9gm5kXV1uTQuMoY=
```

And add it by running:
```
ldapadd -x -D cn=admin,dc=example,dc=com -W -f add_user.ldif
```

### Adding a member group
Create a file _add_group.ldif_:
```
dn: cn=oper,ou=groups,dc=example,dc=com
objectClass: groupofnames
cn: oper
description: All users
member: uid=ygorelik,ou=people,dc=example,dc=com
```

where you add a member line for each user that you want to add to this group. And then run:
```
ldapadd -x -D cn=admin,dc=example,dc=com -W -f add_group.ldif
```

### Taking it for a test-run
Run the following command to see if it's all set up properly:
```
ldapsearch -x -LLL -H ldap:/// -b cn=ygorelik,ou=people,dc=example,dc=com dn memberof
```

And it should yield this result:
```
dn: uid=ygorelik,ou=people,dc=example,dc=com
memberOf: cn=oper,ou=groups,dc=example,dc=com
```
