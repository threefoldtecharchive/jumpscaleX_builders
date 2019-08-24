sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen
export HOME=/root
export LANG=en_US.UTF-8
export LANGUAGE=en_US.UTF-8zdb
export LC_ALL=en_US.UTF-8
. /sandbox/env.sh

cd /sandbox/code/github/threefoldtech/jumpscaleX
git stash; git fetch -v; git pull origin development_jumpscale; git checkout development_jumpscale -f
cd /sandbox/code/github/threefoldtech/digitalmeX
git stash; git fetch -v; git pull origin development_jumpscale; git checkout development_jumpscale -f
cd /sandbox/code/github/threefoldtech/digitalmeX
js_init generate
cd /sandbox/code/github/threefoldtech/jumpscaleX
echo bash >> ~/.profile
groupadd www
useradd -G www www
mkdir -p /etc/resty-auto-ssl
chown -R www:www /etc/resty-auto-ssl
chmod 755 /etc/resty-auto-ssl
openssl req -new -newkey rsa:2048 -days 3650 -nodes -x509 \
-subj '/CN=sni-support-required-for-valid-ssl' \
-keyout /sandbox/cfg/ssl/resty-auto-ssl-fallback.key \
-out /sandbox/cfg/ssl/resty-auto-ssl-fallback.crt
sudo adduser --system --no-create-home --shell /bin/false --group --disabled-login www
mkdir -p /etc/resty-auto-ssl/letsencrypt/certs/
mv /resty-auto-ssl-fallback.key /etc/resty-auto-ssl/letsencrypt/certs/
mv /resty-auto-ssl-fallback.crt /etc/resty-auto-ssl/letsencrypt/certs/
. /sandbox/env.sh; kosmos 'j.servers.threebot.default.start()'
