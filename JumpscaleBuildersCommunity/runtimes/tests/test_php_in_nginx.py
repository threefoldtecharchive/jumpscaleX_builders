import pytest
import os
import requests
import time

from Jumpscale import j


def get_test_nginx_site(www_path="/var/www/html"):
    return (
        """\
    user www-data;
    worker_processes auto;
    pid /run/nginx.pid;

    events {
        worker_connections 768;
        # multi_accept on;
    }

    http {

        server {
        listen 80 default_server;
        listen [::]:80 default_server;

        root %s;

        index index.php index.html index.htm index.nginx-debian.html;

        server_name localhost;

        location / {
            # First attempt to serve request as file, then
            # as directory, then fall back to displaying a 404.
            try_files $uri $uri/ =404;
        }

        location ~ \.php$ {
        fastcgi_split_path_info ^(.+\.php)(/.+)$;

        try_files $fastcgi_script_name =404;

        set $path_info $fastcgi_path_info;
        fastcgi_param PATH_INFO $path_info;

        fastcgi_index index.php;
        include fastcgi.conf;

        fastcgi_pass unix:/var/run/php-fpm.sock;
        }

        location ~ /\.ht {
            deny all;
        }
        }
    }

    """
        % www_path
    )


@pytest.mark.integration
def test_main(self=None):
    """
    to run:

    kosmos 'j.builders.runtime.php._test(name="php_in_nginx")'

    """
    j.builders.web.nginx.install()
    j.builders.runtimes.php.install()

    www_path = self._replace("{DIR_TEMP}/www/")
    j.builders.tools.dir_ensure(www_path)
    nginx_conf = get_test_nginx_site(www_path)
    default_site_path = "/tmp/builders/nginx/conf/nginx-php.conf"
    j.sal.fs.writeFile(default_site_path, contents=nginx_conf)
    j.builders.tools.dir_ensure(j.builders.tools.joinpaths(www_path, "test"))
    j.sal.fs.writeFile(j.builders.tools.joinpaths(www_path, "test", "index.php"), contents="<?php phpinfo(); ?>")

    cmd = j.core.tools.text_replace("{DIR_BASE}/sbin/php-fpm -F -y /sandbox/etc/php-fpm.d/www.conf")
    php_cmd = j.servers.startupcmd.get(name="test_php", cmd_start=cmd, process_strings=[j.core.tools.text_replace("{DIR_BASE}/sbin/php-fpm")])
    cmd = "nginx -c /tmp/builders/nginx/conf/nginx-php.conf -g 'daemon off;'"
    nginx_cmd = j.servers.startupcmd.get(name="test_nginx-php", cmd_start=cmd, cmd_stop="nginx -s stop")

    php_cmd.start()
    nginx_cmd.start()

    # wait until port is ready
    time.sleep(10)

    # test executing the php index file
    res = requests.get("http://localhost/test")
    assert res.status_code == 200, "Failed to retrieve deployed php page. Error: {}".format(res.text)

    j.builders.runtimes.php.stop()
    j.sal.process.killProcessByName("nginx")

