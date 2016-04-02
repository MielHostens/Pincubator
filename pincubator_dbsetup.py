#!/usr/bin/env python
#!/usr/bin/env python
from __future__ import print_function

import mysql.connector
from mysql.connector import errorcode

DB_NAME = 'pincubator'

TABLES = {}
TABLES['tbl_sensordata'] = (
    "CREATE TABLE `tbl_sensordata` ("
    "  `sd_no` int(11) NOT NULL AUTO_INCREMENT,"
    "  `sensor_date` datetime NOT NULL,"
    "  `sensor` int(11) NOT NULL,"
    "  `temp` int(11) NOT NULL,"
    "  `hum` int(11) NOT NULL,"
    "  PRIMARY KEY (`sd_no`)"
    ") ENGINE=InnoDB")

TABLES['tbl_targetdata'] = (
    "CREATE TABLE `tbl_targetdata` ("
    "  `td_no` int(11) NOT NULL AUTO_INCREMENT,"
    "  `day` int(11) NOT NULL,"
    "  `temp` int(11) NOT NULL,"
    "  `hum` int(11) NOT NULL,"
    "  PRIMARY KEY (`td_no`)"
    ") ENGINE=InnoDB")


cnx = mysql.connector.connect(user='root', password='bdyCm1;',host='127.0.0.1')
cursor = cnx.cursor()

def create_database(cursor):
    try:
        cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))
    except mysql.connector.Error as err:
        print("Failed creating database: {}".format(err))
        exit(1)

try:
    cnx.database = DB_NAME    
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_BAD_DB_ERROR:
        create_database(cursor)
        cnx.database = DB_NAME
    else:
        print(err)
        exit(1)


for name, ddl in TABLES.iteritems():
    try:
        print("Creating table {}: ".format(name), end='')
        cursor.execute(ddl)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            print("already exists.")
        else:
            print(err.msg)
    else:
        print("OK")
cursor.close()
cnx.close()

