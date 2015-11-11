FROM webcenter/rancher-stack-base:latest

MAINTAINER Sebastien LANGOUREAUX <linuxworkgroup@hotmail.com>

ENV POSTGRES_VERSION 9.3

ENV DB app
ENV USER admin
ENV GLUSTER_VOLUME dbvol
ENV POSTGRES_BACKUP_SCHEDULE '0 2 * * *'
ENV POSTGRES_BACKUP_DIRECTORY '/data/backup'
ENV POSTGRES_BACKUP_PURGE 8

# Install GPG key
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# Install postgres
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ trusty-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    apt-get update && \
    apt-get install -y --force-yes postgresql-9.3 postgresql-client-9.3 postgresql-contrib-9.3 && \
    /etc/init.d/postgresql stop

# Setting postgres
RUN sed -i -e"s/data_directory =.*$/data_directory = '\/data'/" /etc/postgresql/${POSTGRES_VERSION}/main/postgresql.conf
RUN sed -i -e"s/^#listen_addresses =.*$/listen_addresses = '*'/" /etc/postgresql/${POSTGRES_VERSION}/main/postgresql.conf
RUN echo "host    all    all    0.0.0.0/0    md5" >> /etc/postgresql/${POSTGRES_VERSION}/main/pg_hba.conf
RUN mkdir -p /var/run/postgresql/9.3-main.pg_stat_tmp
RUN chown postgres /var/run/postgresql/9.3-main.pg_stat_tmp
RUN chgrp postgres /var/run/postgresql/9.3-main.pg_stat_tmp

# Install backup tools
WORKDIR /opt
RUN git clone https://github.com/orgrim/pg_back.git
RUN chmod +x /opt/pg_back/pg_back
RUN cp /opt/pg_back/pg_back.conf /etc/postgresql/pg_back.conf


# Add logrorate setting
ADD assets/setup/logrotate-postgres.conf /etc/logrotate.d/postgresql

# Add supervisor setting
ADD assets/setup/supervisor-postgresql.conf /etc/supervisor/conf.d/postgresql.conf

# Add Backuo cron job
ADD assets/setup/cron-postgresql_backup.conf /etc/cron.d/postgresql_backup.conf
RUN chmod 0644 /etc/cron.d/postgresql_backup.conf


# Add main script
ADD assets/init.py /app/init.py
ADD assets/run /app/run
RUN chmod 755 /app/init.py
RUN chmod 755 /app/run
WORKDIR /app

# Add empty file to look if the first time that container is lauched
RUN touch /firstrun

# CLEAN APT
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN mkdir /data


EXPOSE 5432
VOLUME ["/var/log/postgresql", "/etc/postgresql", "/var/run/postgresql/9.3-main.pg_stat_tmp"]
CMD [ "/app/run"]
