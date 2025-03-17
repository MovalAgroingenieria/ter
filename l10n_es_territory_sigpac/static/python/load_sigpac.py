# -*- coding: utf-8 -*-

import sys
import subprocess
import psycopg2

# SHP to SIGPAC table (if the table exists records will be added, otherwise the table will be created and records added afterwards).
#
# Examples:
#
# 1. One SHP:
# python load_sigpac.py 127.0.0.1 5432 v10_cr_campo_cartagena_restored_20221229 odoo10moval odoo10movalEis51n1970molino1750 /tmp/rec_30045_2022_20220113.shp 25830
#
# 2. Two SHP:
# python load_sigpac.py 127.0.0.1 5432 v10_cr_campo_cartagena_restored_20221229 odoo10moval odoo10movalEis51n1970molino1750 /tmp/rec_03142_2022_20220113.shp#/tmp/rec_30045_2022_20220113.shp 25830
#
# 3. Three SHP, a SHP with filter:
# python load_sigpac.py 127.0.0.1 5432 v10_cr_campo_cartagena_restored_20221229 odoo10moval odoo10movalEis51n1970molino1750 '/tmp/rec_03142_2022_20220113.shp#/tmp/rec_30045_2022_20220113.shp("poligono">=529 and "poligono"<=539)#/tmp/rec_30045_2022_20220113.shp' 25830

num_args = len(sys.argv)
if num_args == 8:
    # Get parameters.
    args = sys.argv[1:]
    host = args[0]
    port = args[1]
    dbname = args[2]
    user = args[3]
    password = args[4]
    shptoimport = args[5].split('#')
    srs = args[6]
    # SHP to "ter_gis_sigpac" table.
    for shp in shptoimport:
        condition = ''
        pos_initial_bracket = shp.find('(')
        if pos_initial_bracket != -1:
            pos_final_bracket = shp.find(')')
            if (pos_final_bracket != -1 and
               pos_initial_bracket < pos_final_bracket):
                condition = shp[
                    pos_initial_bracket + 1: pos_final_bracket]
                shp = shp[:pos_initial_bracket]
        list_of_args = ['ogr2ogr', '-f', 'PostgreSQL',
                        "PG:host='{}' port={} dbname='{}' user='{}' password='{}'".format(host, port, dbname, user, password),
                        shp, '-nln', 'ter_gis_sigpac', '-t_srs', 'EPSG:' + str(srs)]
        if condition != '':
            list_of_args.append('-where')
            list_of_args.append(condition)
        exit_code = subprocess.call(list_of_args)
        if exit_code != 0:
            break
    final_message = 'Operation completed successfully.'
    if exit_code:
        final_message = 'Failed to call ogr2ogr.'
    else:
        try:
            connection = psycopg2.connect(host=host, port=port, database=dbname, user=user, password=password)
            cursor = connection.cursor()
            cursor.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY ter_sigpac')
            connection.commit()
            cursor.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY ter_parcel_sigpaclink')
            connection.commit()
            connection.close
        except Exception:
            final_message = 'Failed to refresh materialized views.'
            exit_code = 255
    print(final_message)
    sys.exit(exit_code)
else:
    print('SHP to SIGPAC table, incorrect syntax. Use:\n python load_sigpac.py {host} {port} {dbname} {user} {password} {shp_list_with_optional_condition} {srs}')
    print('\nExample 1 (one SHP):\n')
    print('python load_sigpac.py 127.0.0.1 5432 dbname odoo10moval passwd /tmp/rec_30045_2022_20220113.shp 25830')
    print('\nExample 2 (two SHP):\n')
    print('python load_sigpac.py 127.0.0.1 5432 dbname odoo10moval passwd /tmp/rec_03142_2022_20220113.shp#/tmp/rec_30045_2022_20220113.shp 25830')
    print('\nExample 3 (three SHP, a SHP with filter):\n')
    print('python load_sigpac.py 127.0.0.1 5432 dbname odoo10moval passwd \'/tmp/rec_03142_2022_20220113.shp#/tmp/rec_30045_2022_20220113.shp("poligono">=529 and "poligono"<=539)#/tmp/rec_30045_2022_20220113.shp\' 25830')
    sys.exit(255)
