connect('{{ weblogic_admin }}', '{{ weblogic_admin_pass }}', 't3://{{ admin_server.host }}:7001')
nmEnroll('{{ domains_home }}/{{ domain_name }}', '{{ domains_home }}/{{ domain_name }}/nodemanager')

exit()
