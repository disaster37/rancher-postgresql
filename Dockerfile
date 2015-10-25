FROM webcenter/rancher-stack-base:latest

MAINTAINER Sebastien LANGOUREAUX <linuxworkgroup@hotmail.com>

ENV POSTGRES_VERSION 9.3

# Install postgres
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ trusty-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    apt-get update && \
    apt-get install -y --force-yes postgresql-9.3 postgresql-client-9.3 postgresql-contrib-9.3 && \
    /etc/init.d/postgresql stop

# Setting postgres
RUN sed -i -e"s/data_directory =.*$/data_directory = '\/data'/" /etc/postgresql/${POSTGRES_VERSION}/main/postgresql.conf
RUN sed -i -e"s/^#listen_addresses =.*$/listen_addresses = '*'/" /etc/postgresql/${POSTGRES_VERSION}/main/postgresql.conf
RUN echo "host    all    all    0.0.0.0/0    md5" >> /etc/postgresql/${POSTGRES_VERSION}/main/pg_hba.conf


# Add logrorate setting
ADD assets/setup/logrotate-postgres.conf /etc/logrotate.d/postgresql

# Add supervisor setting
ADD assets/setup/supervisor-postgresql.conf /etc/supervisor/conf.d/postgresql.conf


# Add main script
ADD assets/init.py /app/init.py
RUN chmod 755 /app/init.py

# Add empty file to look if the first time that container is lauched
RUN touch /firstrun

# CLEAN APT
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


EXPOSE 5432
VOLUME ["/data", "/var/log/postgresql", "/etc/postgresql"]
CMD [ "/app/init.py", "start" ]
