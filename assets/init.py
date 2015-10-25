#!/usr/bin/python

import fileinput
import sys
import os
import os.path
import shutil
import re
import subprocess



def replace_all(file, searchRegex, replaceExp):
  """ Replace String in file with regex
  :param file: The file name where you should to modify the string
  :param searchRegex: The pattern witch must match to replace the string
  :param replaceExp: The string replacement
  :return:
  """

  regex = re.compile(searchRegex, re.IGNORECASE)

  f = open(file,'r')
  out = f.readlines()
  f.close()

  f = open(file,'w')

  for line in out:
      if regex.search(line) is not None:
        line = regex.sub(replaceExp, line)

      f.write(line)

  f.close()


def add_end_file(file, line):
    """ Add line at the end of file
    :param file: The file where you should to add line to the end
    :param line: The line to add in file
    :return:
    """
    with open(file, "a") as myFile:
        myFile.write("\n" + line + "\n")



def first_run(user, password, database):
    """ Init the database
    :param user: the database owner
    :param password: the password for user
    :param database: the database name
    :return:
    """

    if user is None or user == "":
      raise Exception("You must set the user")
    if password is None or password == "":
      raise Exception("You must set the password")
    if database is None or database == "":
      raise Exception("You must set the database")

    # We init the database folder if is empty
    if len(os.listdir('/data')) == 0:
      shutil.copytree("/var/lib/postgresql/" + os.getenv('POSTGRES_VERSION') + "/main/", "/data")
      os.system('chown -R postgres /data')
      os.system('chmod -R 700 /data')


    # We create the user in postgres
    query = """DROP ROLE IF EXISTS """ + user + """;
    CREATE ROLE """ + user + """ WITH ENCRYPTED PASSWORD '""" + password + """';
    ALTER USER """ + user + """ WITH ENCRYPTED PASSWORD '""" + password + """';
    ALTER ROLE """ + user + """ WITH SUPERUSER;
    ALTER ROLE """ + user + """ WITH LOGIN;"""
    os.system("setuser postgres psql -q " + query)

    # We create the database
    query = """CREATE DATABASE """ + database + """ WITH OWNER=""" + user + """ ENCODING='UTF8';
    GRANT ALL ON DATABASE """ + database + """ TO """ + user
    os.system("setuser postgres psql -q " + query)

    # We remove the marker to say it's the first run
    os.remove('/firstrun')


# Start
if(len(sys.argv) > 1 and sys.argv[1] == "start"):

    # First we mount the gluster storage
    p = subprocess.Popen('mount -t glusterfs gluster:/ranchervol /data', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
      raise Exception("We can't mount glusterfs volume. Are you sure you have linked gluster service with name 'gluster' ?")
    
    # Init database if needed
    if os.path.isfile('/firstrun'):
      first_run(os.getenv('USER'), os.getenv('PASS'), os.getenv('DB'))

    # Start services
    os.system("/usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf")
    


    
