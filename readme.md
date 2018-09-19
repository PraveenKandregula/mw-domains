Below variables are defined in secrets.yml <br />
    sysdba_passwd: <br />
    datasource_password: <br />
    weblogic_admin: <br />
    weblogic_admin_pass: <br />

Follow below syntax to run the playbook. <br />
    ansible-playbook soa-12212-domain.yml -i inventory --key-file=~/aws-key.pem --vault-password-file=~/.vault -v <br />

Open issues: <br />
	Integrations are failing. <br />
	Startup role fails while starting the managed servers for the first time after domain creation. Strangely, managed servers are getting started from console and subsequent startup through startup role is going through. <br />
