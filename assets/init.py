#!/usr/bin/python

import fileinput
import sys
import os
import os.path
import shutil
import re
import subprocess
import time
from threading import Thread


class ThreadQuery(Thread):

  def __init__(self, user, password, database):
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

    Thread.__init__(self)
    self.user = user
    self.password = password
    self.database = database

  def run(self):
    
    print("Wait 30s that postgres start \n")
    time.sleep(30)


    # We create the user in postgres
    query = "DROP ROLE IF EXISTS " + self.user + ";CREATE ROLE " + self.user + " WITH ENCRYPTED PASSWORD '" + self.password + "';ALTER USER " + self.user + " WITH ENCRYPTED PASSWORD '" + self.password + "';ALTER ROLE " + self.user + " WITH SUPERUSER;ALTER ROLE " + self.user + " WITH LOGIN;"
    os.system("su - postgres -c \"psql -q -c \\\"" + query + "\\\"\"")

    # We create the database
    query = "CREATE DATABASE " + self.database + " WITH OWNER=" + self.user + " ENCODING='UTF8';"
    os.system("su - postgres -c \"psql -q -c \\\"" + query + "\\\"\"")

    # We set the right
    query = "GRANT ALL ON DATABASE " + self.database + " TO " + self.user + ";"
    os.system("su - postgres -c \"psql -q -c \\\"" + query + "\\\"\"")

    # We remove the marker to say it's the first run
    os.remove('/firstrun')

    print("Database and user is setting on Postgresql !\n")
    


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

def init_data_folder():
    # We init the database folder if is empty
    if len(os.listdir('/data')) < 3:
      os.system('cp -R /var/lib/postgresql/' + os.getenv('POSTGRES_VERSION') + '/main/* /data/')
      os.system('chown -R postgres /data')
      os.system('chmod -R 700 /data')
      print("Data folder for Postgresql is initialized\n")
    else:
      print("Data folder for Postgresql is already initialized\n")




# Start
if(len(sys.argv) > 1 and sys.argv[1] == "start"):

    # First we mount the gluster storage
    loop = True
    while(loop):
      p = subprocess.Popen('mount -t glusterfs gluster:/ranchervol /data', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      output, error = p.communicate()
      if p.returncode != 0:
        print("We can't mount glusterfs volume. Are you sure you have linked gluster service with name 'gluster' ? We retry in 60 seconds \n")
        print("Output : " + output + "\n")
        print("Error : " + error + "\n")
        time.sleep(60)
      else:
        loop = False
        print("Gluster volume is mounted \n")
    
    # Init data folder
    init_data_folder()

    # Start thread to create database
    # Init database if needed
    if os.path.isfile('/firstrun'):
      thread_query = ThreadQuery(os.getenv('USER'), os.getenv('PASS'), os.getenv('DB'))
      thread_query.start()

    # Start services
    os.system("/usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf")
    

    


    
