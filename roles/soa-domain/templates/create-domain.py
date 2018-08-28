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

admin_server = {{ admin_server }}
managed_servers = {{ managed_servers }}
cluster = "{{ cluster_name }}"

readTemplate(weblogic_template)
setOption('ServerStartMode', 'prod')
setOption('DomainName',domain_name)
setOption('OverwriteDomain','true')

print 'Configuring Admin server...'
cd('/Servers/AdminServer')
create('AdminServer','SSL')
cd('SSL/AdminServer')
set('Enabled', 'False')
set('HostNameVerificationIgnored', 'True')
cd('/Security/base_domain/User/weblogic')
cmo.setName('{{ weblogic_admin }}')
cmo.setUserPassword('{{ weblogic_admin_pass }}')
writeDomain(domain_configuration_home)
closeTemplate()
print 'Admin server has been configured\n'

readDomain(domain_configuration_home)
addTemplate(soa_template)
setOption('AppDir', domain_application_home)

#JDBC
print 'connection string ' + data_source_url
cd('/')
print 'Configuring JDBC...'
jdbcsrcs=cmo.getJDBCSystemResources()
cd('/JDBCSystemResource/LocalSvcTblDataSource/JdbcResource/LocalSvcTblDataSource/JDBCDriverParams/NO_NAME_0')
set('URL',data_source_url)
set('PasswordEncrypted','{{ datasource_password }}')
cd('Properties/NO_NAME_0/Property/user')
set('Value',data_source_user_prefix + '_STB')
getDatabaseDefaults()

for sr in range(len(jdbcsrcs)):
    s = jdbcsrcs[sr]
    cd('/')
    print 'Changing to XA for '+s.getName()
    cd('/JDBCSystemResource/'+s.getName()+'/JdbcResource/'+s.getName()+'/JDBCDriverParams/NO_NAME_0')
    set('DriverName','oracle.jdbc.xa.client.OracleXADataSource')
    set('UseXADataSourceInterface','True')
    cd('/JDBCSystemResource/'+s.getName()+'/JdbcResource/'+s.getName()+'/JDBCDataSourceParams/NO_NAME_0')
    set('GlobalTransactionsProtocol','TwoPhaseCommit')

updateDomain()
print 'JDBC has been configured'

print '\n\nAdding machines to domain...\n'
try:
    servers={{ domain_hosts }}
    #readDomain(domain_configuration_home)
    for i in servers :
        cd('/')
        #cmo.createUnixMachine(i)
        create(i,'UnixMachine')
        cd('/UnixMachines/'+i)
        nmgr = create(i,'NodeManager')
        nmgr.setNMType('Plain')
        nmgr.setListenAddress(i)
        nmgr.setListenPort(int('{{ node_manager_listen_port }}'))
        nmgr.setDebugEnabled(false)
        print 'Added machine:' + i + ' to domain'
	updateDomain()
    setServerGroups('AdminServer',["WSM-CACHE-SVR" , "WSMPM-MAN-SVR" , "JRF-MAN-SVR"])
    cd('/SecurityConfiguration/' + domain_name)
    cmo.setNodeManagerUsername('{{ weblogic_admin }}')
    cmo.setNodeManagerPasswordEncrypted('{{ weblogic_admin_pass }}')
    set('CrossDomainSecurityEnabled',true)
    updateDomain()
    print '\nAdded machines to domain'
except Exception,e:
    print str(e)
    dumpStack()
    print 'Failed at adding machine to domain'

print 'Adding cluster to domain'
cd('/')
create(cluster, 'Cluster')
updateDomain()

print 'Assigning admin server to a machine'
cd('/')
cd('Server/' + admin_server['name'] )
set('Machine', str(admin_server['machine']))

print 'Creating managed servers'
for m in managed_servers : 
    cd('/')
    delete('soa_server1','Server')
    create(m['name'],'Server')
    cd('/Servers/' + m['name'])
    cmo.setListenAddress(m['machine'])
    cmo.setListenPort(int(m['port']))
    set('Machine',m['machine'])
    setServerGroups(m['name'], ['SOA-MGD-SVRS'])
    cd('/')
    assign('Server',m['name'],'Cluster',cluster)
    print 'Created ' + m['name']
    updateDomain()

closeDomain()
