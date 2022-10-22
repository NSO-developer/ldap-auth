all:
	ncs-setup --dest .
	$(MAKE) -C packages/ldap-config/src all

clean:
	$(MAKE) -C packages/ldap-config/src clean

stop:
	ncs --stop

reset:
	ncs-setup --reset

cli:
	ncs_cli -Cu admin
