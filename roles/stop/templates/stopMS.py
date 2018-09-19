nmConnect('{{ weblogic_admin }}', '{{ weblogic_admin_pass }}', '{{ inventory_hostname }}', '5556', '{{ domain_name }}', '{{ domains_home }}/{{ domain_name }}', 'SSL')
status = nmServerStatus('{{ server }}')

if status == 'RUNNING' :
  nmKill('{{ server }}') 
else:
  print '{{ server }} is not running'

exit()
