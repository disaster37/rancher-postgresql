#!/usr/bin/python

import fileinput
import sys
import os
import os.path
import shutil
import re
import subprocess
import time



class ServiceRun():



  def init_database(self, user,password, database):

    if user is None or user == "":
      raise Exception("You must set the user")
    if password is None or password == "":
      raise Exception("You must set the password")
    if database is None or database == "":
      raise Exception("You must set the database")

    print("Wait 30s that postgres start \n")
    time.sleep(30)


    # We create the user in postgres
    query = "DROP ROLE IF EXISTS " + user + ";CREATE ROLE " + user + " WITH ENCRYPTED PASSWORD '" + password + "';ALTER USER " + user + " WITH ENCRYPTED PASSWORD '" + password + "';ALTER ROLE " + user + " WITH SUPERUSER;ALTER ROLE " + user + " WITH LOGIN;"
    os.system("su - postgres -c \"psql -q -c \\\"" + query + "\\\"\"")

    # We create the database
    query = "CREATE DATABASE " + database + " WITH OWNER=" + user + " ENCODING='UTF8';"
    os.system("su - postgres -c \"psql -q -c \\\"" + query + "\\\"\"")

    # We set the right
    query = "GRANT ALL ON DATABASE " + database + " TO " + user + ";"
    os.system("su - postgres -c \"psql -q -c \\\"" + query + "\\\"\"")



    print("Database and user is setting on Postgresql !\n")

  def init_data_folder(self):
    # We init the database folder if is empty
    if len(os.listdir('/data')) < 3:
      os.system('cp -R /var/lib/postgresql/' + os.getenv('POSTGRES_VERSION') + '/main/* /data/')
      os.system('chown -R postgres /data')
      os.system('chmod -R 700 /data')
      print("Data folder for Postgresql is initialized\n")
    else:
      print("Data folder for Postgresql is already initialized\n")

  def set_backup_policy(self, schedule, backup_directory, purge):


    # We set backup setting en cron
    if os.getenv('POSTGRES_BACKUP_SCHEDULE') is not None and os.getenv('POSTGRES_BACKUP_SCHEDULE') != 'disabled':
      if backup_directory is None or backup_directory == '':
        raise KeyError("You must set the backup directory")
      if purge is None or purge < 0:
        raise KeyError("You must set the purge policy")

      # We set the backup directory
      replace_all('/etc/postgresql/pg_back.conf', 'PGBK_BACKUP_DIR=.*', 'PGBK_BACKUP_DIR=' + backup_directory)

      # We set the purge policy
      replace_all('/etc/postgresql/pg_back.conf', 'PGBK_PURGE=.*', 'PGBK_PURGE=' + purge)

      replace_all('/etc/cron.d/postgresql_backup.conf', '.*' + re.escape('/opt/pg_back/pg_back') + '.*', schedule + " postgres /opt/pg_back/pg_back")

      print("Cron backup policy updated")

    # We remove the cron
    else:
      replace_all('/etc/cron.d/postgresql_backup.conf', re.escape('/opt/pg_back/pg_back'), '')
      print("Cron backup policy disabled")






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





if(len(sys.argv) > 1 and sys.argv[1] == "init"):
    # First we mount the gluster storage
    loop = True
    while(loop):
      p = subprocess.Popen('mount -t glusterfs storage:' + os.getenv('GLUSTER_VOLUME')  + ' /data', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      output, error = p.communicate()
      if p.returncode != 0:
        print("We can't mount glusterfs volume. Are you sure you have linked gluster service with name 'storage' ? We retry in 60 seconds \n")
        print("Output : " + output + "\n")
        print("Error : " + error + "\n")
        time.sleep(60)
      else:
        loop = False
        print("Gluster volume is mounted \n")

    # Init data folder
    service = ServiceRun()
    if os.path.isfile('/firstrun'):
      service.init_data_folder()

    # Set backup policy
    service.set_backup_policy(os.getenv('POSTGRES_BACKUP_SCHEDULE'), os.getenv('POSTGRES_BACKUP_DIRECTORY'), os.getenv('POSTGRES_BACKUP_PURGE'))

# Start
if(len(sys.argv) > 1 and sys.argv[1] == "start"):


    # Init database account if needed
    if os.path.isfile('/firstrun'):
        if os.getenv('PASS') is None:
            program = ['pwgen',13,1]
            password = subprocess.check_output(program)
            print("The password is : " + password)
        else:
	        password = os.getenv('PASS')


        service = ServiceRun()
        service.init_database(os.getenv('USER'),password, os.getenv('DB'))

        os.remove('/firstrun')







