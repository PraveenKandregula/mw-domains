#Collect Templates
FMW_HOME = '{{ middleware_home }}'
WLS_TEMPLATE  = FMW_HOME + '/wlserver/common/templates/wls/wls.jar'
SOA_TEMPLATES = [FMW_HOME + '/soa/common/templates/wls/oracle.soa_template.jar', FMW_HOME + '/soa/common/templates/wls/oracle.soa.fp_template.jar']
STB_PASSWORD = '{{ datasource_password }}'
SCHEMA_PREFIX = '{{ soa_repo_preffix }}'
STB_USERNAME = SCHEMA_PREFIX + '_STB'
DOMAIN_NAME = '{{ domain_name }}'
ASERVER = {{ admin_server }}
MSERVER = {{ managed_servers }}
CLUSTER = {{ cluster }}
#NMANAGER = [{'name':'54.224.116.223', 'host':'54.224.116.223', 'port':'5556'}]
LB_URL = 'soa-domain.praveen.com'
PORT_NUMBER = '8080'
WLS_USERNAME = '{{ weblogic_admin }}' 
WLS_PASSWORD = '{{ weblogic_admin_pass }}'
DOMAIN_HOME = FMW_HOME + '/../domains/' + DOMAIN_NAME
DB_HOST = '{{ dbserver_name }}'
DB_PORT = '{{ dbserver_port }}'
DB_SERVICE = '{{ dbserver_service }}'

#Define functions
def f_updateJDBC():
  cd('/')
  print 'JDBC configuration starts here'
  jdbcsrcs=cmo.getJDBCSystemResources()
  try:
    cd('/JDBCSystemResource/LocalSvcTblDataSource/JdbcResource/LocalSvcTblDataSource/JDBCDriverParams/NO_NAME_0')
    set('URL','jdbc:oracle:thin:@//' + DB_HOST + ':' + DB_PORT + '/' + DB_SERVICE)
    set('PasswordEncrypted',STB_PASSWORD)
    cd('Properties/NO_NAME_0/Property/user')
    set('Value',STB_USERNAME)
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
    
	print 'JDBC configuration has been completed\n'
  except Exception,e: 
    print str(e)
    print 'ERROR: f_updateJDBC() !'
    dumpStack()

def f_clean():
  try:
    cd('/')
    dummysrvrs = ['soa_server1']
    srvrs=cmo.getServers()
    for s in range(len(srvrs)):
      srv = srvrs[s]
      if srv.getName() in dummysrvrs:
        srv.setName('SOA_MS1')
        
  except Exception,e: 
    print str(e)
    print 'ERROR: f_clean() !'
    dumpStack()
    
def f_createNM():
  try:
    for nm in range(len(MSERVER)):
      cd('/') 
      create(MSERVER[nm]['machine'], 'UnixMachine')
      cd('UnixMachine/'+MSERVER[nm]['machine'])
      nmgr = create(MSERVER[nm]['machine'],'NodeManager')
      nmgr.setListenAddress(MSERVER[nm]['host'])
      nmgr.setListenPort(5556) 
    print 'NM module has been completed successfully\n'
  except Exception,e: 
    print str(e)
    print 'ERROR: f_createNM() !'
    dumpStack()

def f_addServers():
  print 'Add servers module starts here'
  try:
    for m in range(len(MSERVER)):
      cd('/')
      if MSERVER[m]['name'] in ["SOA_MS1"]: 
        f_clean()
      else:
        create(MSERVER[m]['name'], 'Server')  
      cd('/Servers/'+MSERVER[m]['name'])
      set('ListenAddress',MSERVER[m]['host'])
      set('ListenPort'   ,int(MSERVER[m]['port']))
      set('Machine',MSERVER[m]['machine'])
      setServerGroups(MSERVER[m]['name'],["SOA-MGD-SVRS"])
      print 'Added ' + MSERVER[m]['name']
       
    cd('/')
    print 'Adding cluster'
    clus = create(CLUSTER['name'], 'Cluster')
    clus.setClusterMessagingMode('unicast')
    clus.setFrontendHost(LB_URL)
    clus.setFrontendHTTPPort(int(PORT_NUMBER))
    clus.setClusterAddress(CLUSTER['lb_url'])
    clus.setTxnAffinityEnabled(true)
    print 'Cluster has been added'
     
    for m in MSERVER:
      assign('Server',m['name'],'Cluster',CLUSTER['name'])
      cd('/Servers/'+m['name'])
      set('Machine',m['machine'])
      print m['name'] + ' has been added to ' + CLUSTER['name']

    print 'Add servers module has been completed\n'
  except Exception,e: 
    print str(e)
    print 'ERROR: f_addServers() !'
    dumpStack()

def f_createDomain():
  print '*********** Script execution starts here***********'
  try:
    readTemplate(WLS_TEMPLATE)
    setOption('ServerStartMode', 'prod')
    setOption('DomainName',DOMAIN_NAME)
    setOption('OverwriteDomain','true')
  
    cd('/')
    cd('/Servers/AdminServer')
    set('Name','AdminServer')
    set('ListenAddress',ASERVER['host'])
    #set('ListenPort'   ,int(ASERVER['port']))
 
    cd('/')
    cd('/Servers/AdminServer')
    create('AdminServer','SSL')
    cd('SSL/AdminServer')
    set('Enabled', 'False')
    set('HostNameVerificationIgnored', 'True')
    cd('/Security/base_domain/User/weblogic')
    cmo.setName(WLS_USERNAME)
    cmo.setUserPassword(WLS_PASSWORD)
    
    writeDomain(DOMAIN_HOME)
    closeTemplate()
    print 'Admin completed\n'
    readDomain(DOMAIN_HOME)
    for t in range(len(SOA_TEMPLATES)):
      print 'adding ' + SOA_TEMPLATES[t]
      addTemplate(SOA_TEMPLATES[t])
      print 'added ' + SOA_TEMPLATES[t] + '\n'
      
    f_updateJDBC()
    f_createNM()
    print 'Post domain conguration starts here'
    setServerGroups('AdminServer',["WSM-CACHE-SVR" , "WSMPM-MAN-SVR" , "JRF-MAN-SVR"])
    cd('/SecurityConfiguration/'+DOMAIN_NAME)
    cmo.setNodeManagerUsername(WLS_USERNAME)
    cmo.setNodeManagerPasswordEncrypted(WLS_PASSWORD)
    set('CrossDomainSecurityEnabled',true)
    print 'Post domain configuration completed\n'
  
    f_addServers()
    updateDomain()
    closeDomain()
    
  except Exception,e: 
    print str(e)
    print 'ERROR: f_createDomain()'
    dumpStack()

#Execute Functions
f_createDomain()
print '***********Script execution completed***********'
