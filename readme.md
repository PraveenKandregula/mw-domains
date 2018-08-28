Below variables are defined in secrets.yml
    sysdba_passwd:
    datasource_password: 
    weblogic_admin:
    weblogic_admin_pass: 

Follow below syntax to run the playbook. 
    ansible-playbook soa-12212-domain.yml -i inventory --key-file=~/aws-key.pem --vault-password-file=~/.vault -v
