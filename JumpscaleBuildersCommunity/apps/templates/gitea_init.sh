LOGIN_CFG='{"Provider":"itsyou.online","ClientID":"'$IYO_CLIENT_ID'","ClientSecret":"'$IYO_CLIENT_SECRET'","OpenIDConnectAutoDiscoveryURL":"","CustomURLMapping":null}'
STMT="INSERT INTO login_source (type, name, is_actived, cfg, created_unix, updated_unix) \
    VALUES (6, 'Itsyou.online', TRUE, '$LOGIN_CFG', extract('epoch' from CURRENT_TIMESTAMP) , extract('epoch' from CURRENT_TIMESTAMP)) \
        ON CONFLICT (name) DO UPDATE set cfg = '$LOGIN_CFG';"

sudo -u postgres /sandbox/bin/psql gitea -c "$STMT"
