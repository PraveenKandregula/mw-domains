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
aia_template=middleware_home + '/soa/common/templates/wls/oracle.soa.fp_template.jar'

admin_server = {{ admin_server }}
managed_servers = {{ managed_servers }}
cluster_det = {{ cluster }}

#Functions here
def jdbcConfig():
  print 'Configuring JDBC...'
  print 'connection string ' + data_source_url
  cd('/')
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
    if s.getName() in ["EDNDataSource","wlsbjmsrpDataSource","OraSDPMDataSource","SOADataSource","BamDataSource"]:
      print 'Changing to XA for '+s.getName()
      cd('/JDBCSystemResource/'+s.getName()+'/JdbcResource/'+s.getName()+'/JDBCDriverParams/NO_NAME_0')
      set('DriverName','oracle.jdbc.xa.client.OracleXADataSource')
      set('UseXADataSourceInterface','True')
      cd('/JDBCSystemResource/'+s.getName()+'/JdbcResource/'+s.getName()+'/JDBCDataSourceParams/NO_NAME_0')
      set('GlobalTransactionsProtocol','TwoPhaseCommit')

  updateDomain()
  print 'JDBC has been configured\n'

def createNodeManager():
  print 'Configuring Node manager'
  servers={{ domain_hosts }}
  for i in servers :
    cd('/')
    create(i,'UnixMachine')
    cd('/UnixMachines/'+i)
    nmgr = create(i,'NodeManager')
    nmgr.setListenAddress(i)
    nmgr.setListenPort(int('{{ node_manager_listen_port }}'))

  print'Node managers have been added\n'
  setServerGroups('AdminServer',["WSM-CACHE-SVR" , "WSMPM-MAN-SVR" , "JRF-MAN-SVR"])
  cd('/SecurityConfiguration/' + domain_name)
  cmo.setNodeManagerUsername('{{ weblogic_admin }}')
  cmo.setNodeManagerPasswordEncrypted('{{ weblogic_admin_pass }}')
  set('CrossDomainSecurityEnabled',true)
  updateDomain()
  
def addManagedServers():
  print 'Creating cluster'
  cd('/')
  cluster1 = create(cluster_det['name'], 'Cluster')
  cluster1.setClusterMessagingMode('unicast')
  cluster1.setFrontendHost(cluster_det['lb_url'])
  cluster1.setFrontendHTTPPort(int(cluster_det['port']))
  cluster1.setClusterAddress(cluster_det['lb_url'])
  cluster1.setTxnAffinityEnabled(true)
  print 'Creating managed servers'
  for m in managed_servers :
    cd('/')
    print 'Creating ' + m['name']
    if m['name'] == "SOA_MS1" :
      cd('/Server/soa_server1')
      cmo.setName('SOA_MS1')
    else :
      create(m['name'],'Server')
      cd('/Servers/'+m['name'])
    set('ListenAddress', (m['machine']))
    set('ListenPort', (int(m['port'])))
    set('Machine',m['machine'])
    setServerGroups(m['name'], ['SOA-MGD-SVRS'])
    assign('Server',m['name'],'Cluster',cluster_det['name'])
    updateDomain()
    print 'Created ' + m['name'] + ' on ' + m['machine']

  print 'Added all managed servers'

def createDomain():
  readTemplate(weblogic_template)
  setOption('ServerStartMode', 'prod')
  setOption('DomainName',domain_name)
  setOption('OverwriteDomain','true')

  print '\nConfiguring Admin server...'
  cd('/Servers/AdminServer')
  set('Name','AdminServer')
  set('ListenAddress',admin_server['machine'])
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
  addTemplate(aia_template)
  setServerGroups('AdminServer',["WSM-CACHE-SVR" , "WSMPM-MAN-SVR" , "JRF-MAN-SVR"])
  cd('/SecurityConfiguration/' + domain_name)
  setOption('AppDir', domain_application_home)
  
  jdbcConfig()
  #createNodeManager()
  addManagedServers()
  updateDomain()
  closeDomain()

#Execution starts here
createDomain()
