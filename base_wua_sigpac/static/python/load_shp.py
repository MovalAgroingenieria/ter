# -*- coding: utf-8 -*-

import sys
import subprocess

# SHP to PostgreSQL (if the table exists records will be added, otherwise the table will be created and records added afterwards).
#
# Examples:
#
# No filter:
# python load_shp.py 127.0.0.1 5432 v10_cr_campo_cartagena_restored_20221229 odoo10moval odoo10movalEis51n1970molino1750 /tmp/rec_30045_2022_20220113.shp wua_gis_sigpac 25830
#
# Filter (last argument):
# python load_shp.py 127.0.0.1 5432 v10_cr_campo_cartagena_restored_20221229 odoo10moval odoo10movalEis51n1970molino1750 /tmp/rec_30045_2022_20220113.shp wua_gis_sigpac 25830 '"poligono">=529 and "poligono"<=539'

num_args = len(sys.argv)
if num_args == 9 or num_args == 10:
    args = sys.argv[1:]
    host = args[0]
    port = args[1]
    dbname = args[2]
    user = args[3]
    password = args[4]
    shp = args[5]
    table = args[6]
    srs = args[7]
    condition = ''
    if num_args == 10:
        condition = args[8]
    list_of_args = ['ogr2ogr', '-f', 'PostgreSQL',
                    "PG:host='{}' port={} dbname='{}' user='{}' password='{}'".format(host, port, dbname, user, password),
                    shp, '-nln', table, '-t_srs', 'EPSG:' + str(srs)]
    if condition != '':
        list_of_args.append('-where')
        list_of_args.append(condition)
    exit_code = subprocess.call(list_of_args)
    final_message = 'Operation completed successfully.'
    if exit_code:
        final_message = 'Failed to call ogr2ogr.'
    sys.exit(exit_code)
else:
    print 'SHP to PostgreSQL, incorrect sintax. Use:\npython load_shp.py {host} {port} {dbname} {user} {password} {shp} {table} {srs} [{\'condition\'}]'
    print '\nExample 1 (no filter):\n'
    print 'python load_shp.py 127.0.0.1 5432 v10_cr_campo_cartagena_restored_20221229 odoo10moval odoo10movalEis51n1970molino1750 /tmp/rec_30045_2022_20220113.shp wua_gis_sigpac 25830'
    print '\nExample 2 (with filter):\n'
    print 'python load_shp.py 127.0.0.1 5432 v10_cr_campo_cartagena_restored_20221229 odoo10moval odoo10movalEis51n1970molino1750 /tmp/rec_30045_2022_20220113.shp wua_gis_sigpac 25830 \'"poligono">=529 and "poligono"<=539\''
    sys.exit(255)
