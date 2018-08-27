db_server_name = '{{ dbserver_name }}'
db_server_port = '{{ dbserver_port }}'
db_service = '{{ dbserver_service }}'
data_source_url='jdbc:oracle:thin:@//' + db_server_name + ':' + db_server_port + '/' + db_service
data_source_user_prefix= '{{ soa_repo_preffix }}'
data_source_test='SQL SELECT 1 FROM DUAL'

domain_application_home = '{{ applications_home }}/{{ domain_name }}'
domain_configuration_home = '{{ domains_home }}/{{ domain_name }}'
domain_name = '{{ domain_name }}'
java_home = '/bin/java'
middleware_home = '{{ middleware_home }}'
#weblogic_home = '{{ weblogic_home }}'

weblogic_template=middleware_home + '/wlserver/common/templates/wls/wls.jar'
soa_template=middleware_home + '/soa/common/templates/wls/oracle.soa_template.jar'

readTemplate(weblogic_template)
setOption('DomainName', domain_name)
setOption('OverwriteDomain', 'true')
setOption('JavaHome', java_home)
setOption('ServerStartMode', 'prod')

cd('/Security/base_domain/User/weblogic')
cmo.setName('{{ weblogic_admin }}')
cmo.setUserPassword('{{ weblogic_admin_pass }}')
cd('/')

writeDomain(domain_configuration_home)
closeTemplate()

readDomain(domain_configuration_home)
addTemplate(soa_template)
setOption('AppDir', domain_application_home)

jdbcsystemresources = cmo.getJDBCSystemResources()
for jdbcsystemresource in jdbcsystemresources:
    cd ('/JDBCSystemResource/' + jdbcsystemresource.getName() + '/JdbcResource/' + jdbcsystemresource.getName() + '/JDBCConnectionPoolParams/NO_NAME_0')
    cmo.setInitialCapacity(1)
    cmo.setMaxCapacity(15)
    cmo.setMinCapacity(1)
    cmo.setStatementCacheSize(0)
    cmo.setTestConnectionsOnReserve(java.lang.Boolean('false'))
    cmo.setTestTableName(data_source_test)
    cmo.setConnectionCreationRetryFrequencySeconds(30)
    cd ('/JDBCSystemResource/' + jdbcsystemresource.getName() + '/JdbcResource/' + jdbcsystemresource.getName() + '/JDBCDriverParams/NO_NAME_0')
    cmo.setUrl(data_source_url)
    cmo.setPasswordEncrypted('{{ datasource_password }}')
   
    cd ('/JDBCSystemResource/' + jdbcsystemresource.getName() + '/JdbcResource/' + jdbcsystemresource.getName() + '/JDBCDriverParams/NO_NAME_0/Properties/NO_NAME_0/Property/user')
    cmo.setValue(cmo.getValue().replace('DEV',data_source_user_prefix))
    cd('/')

for server in {{ domain_hosts }} :
    create(server,'UnixMachine')
    cd('/UnixMachine/' + server)
    create(server,'NodeManager')
    cd('NodeManager/' + server)
    cmo.setNMType('SSL')
    cmo.setListenAddress(server)
    cmo.setListenPort({{ node_manager_listen_port }})
    cd("/SecurityConfiguration/" + domain_name)
    cmo.setNodeManagerUsername('{{ weblogic_admin }}')
    cmo.setNodeManagerPasswordEncrypted('{{ weblogic_admin_pass }}')
    cd('/')

admin_server = {{ admin_server }}
managed_servers = {{ managed_servers }}
cluster = {{ cluster_name }} 
cd('Server/' + admin_server['name'] )
set('Machine', str(admin_server['machine']))
#cmo.setHostnameVerifier(None)
print ('\nCreate '+cluster)
cd('/')
create(cluster, 'Cluster')
updateDomain()
closeDomain()

readDomain(domain_configuration_home)
cd('/')

for m in managed_servers : 
    cmo.createServer(m['name'])
    cd('/Servers/' + m['name'])
    cmo.setListenAddress(m['machine'])
    cmo.setListenPort(m['port'])
    set('Machine',m['machine'])
    setServerGroups(m['name'], ['SOA-MGD-SVRS'])
    cd('/')
    assign('Server',newSrvName,'Cluster',cluster)
    cd('/')

updateDomain()
closeDomain()
