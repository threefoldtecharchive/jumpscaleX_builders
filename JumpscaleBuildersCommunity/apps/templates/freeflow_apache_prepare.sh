set -x
echo "##### direct apache2 to new php directory under sandbox #######"
echo 'ServerRoot "/sandbox/etc/apache2"' >> /sandbox/etc/apache2/apache2.conf
echo 'PHPINIDir /sandbox/etc/php/7.2/apache2' >> /sandbox/etc/apache2/apache2.conf

sed -i 's#; extension_dir = "./"#extension_dir = "/sandbox/usr/lib/php/20170718"#g' /sandbox/etc/php/7.2/apache2/php.ini
sed -i 's#;include_path = ".:/usr/share/php"#include_path = ".:/sandbox/usr/share/php"#g' /sandbox/etc/php/7.2/apache2/php.ini

source /sandbox/etc/apache2/envvars
# change modules path to new one in /sandbox
for i in $(grep '/usr/lib/apache2' -r /sandbox/  | awk '{print $1}'|awk -F: '{print $1}'|grep -v Binary) ; do echo $i;  sed -i 's/ \/usr\/lib\/apache2\/modules/ \/sandbox\/usr\/lib\/apache2\/modules/g' $i; done

mkdir -p /var/www/html/

if [ ! -d /var/www/html/humhub ]; then
    wget https://www.humhub.org/en/download/package/humhub-1.3.12.tar.gz -O /var/www/html/humhub-1.3.12.tar.gz > /dev/null
    cd /var/www/html;tar -xvf humhub-1.3.12.tar.gz > /dev/null && rm humhub-1.3.12.tar.gz
    mv humhub-1.3.12 humhub
fi

echo \"ServerName localhost\"  > /sandbox/etc/apache2/conf-available/fqdn.conf
#/sandbox/bin/a2enconf fqd

cd /sandbox/etc/php/7.2/mods-available
for i in mysqlnd.ini opcache.ini pdo.ini ; do mv $i 10-$i;done
