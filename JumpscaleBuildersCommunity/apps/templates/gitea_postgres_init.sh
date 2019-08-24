adduser --system --quiet --home /sandbox --no-create-home --shell /bin/bash --group --gecos psql_admin postgres || true
cd /sandbox
mkdir -p log
mkdir -p apps/psql/data
chown -R postgres apps/psql/data
sudo -u postgres /sandbox/bin/initdb -D /sandbox/apps/psql/data/ -E utf8 --locale=en_US.UTF-8 || true
sudo -u postgres /sandbox/bin/pg_ctl start -D /sandbox/apps/psql/data
