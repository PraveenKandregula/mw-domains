Below variables are defined in secrets.yml
    sysdba_passwd:
    datasource_password: 
    weblogic_admin:
    weblogic_admin_pass: 

Follow below syntax to run the playbook. 
    ansible-playbook soa-12212-domain.yml -i inventory --key-file=~/aws-key.pem --vault-password-file=~/.vault -v

Open issues:
	Integrations are failing. <br />
	Startup role fails while starting the managed servers for the first time after domain creation. Strangely, managed servers are getting started from console and subsequent startup through startup role is going through. 
