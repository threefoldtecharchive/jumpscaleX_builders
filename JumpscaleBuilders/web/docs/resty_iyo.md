## Itsyou.online authentication for resty

This introduces how to use [itsyou.online authentication for resty ](lua-resty-iyo-auth) and how to deal with the jwt after login to get some user info.

The authentication is done using `access` directive [access_by_lua](https://github.com/openresty/lua-nginx-module#access_by_lua), and `lua-resty-iyo-auth` package provide some helper lua files to be used with it, a path is protected using access_by_lua, if the user is not logged in, he would be redirected to itsyou.online, then to the callback url configured in nginx config in case of successful login.


In jumpscale, `lua-resty-iyo-auth` will be installed by default when installing lua/openresty using:

`j.builders.runtimes.lua.install()`


We will need to get an itsyou.online organization (client id) and secret to use them in nginx config, [see how to get them here](iyo_api_key.md).


Now we need to create or update our nginx config, a typical configuration would be like:

```conf
events {
    worker_connections 128;
}

# useful for debugging
error_log <log_file_path>;

http {
    # needed by lua-resty-http
    resolver 8.8.8.8 4.2.2.2 ipv6=off;
    resolver_timeout 5s;
    lua_ssl_trusted_certificate '/sandbox/cfg/ssl/certs/ca-certificates.crt';
    lua_ssl_verify_depth 2;

    server {
        listen 8080;

        # lua-resty-sesion config
        set $session_secret '<any_strong_secret>';

        # oauth config
        set $iyo_organization '<organization_name>';
        set $iyo_secret '<client_secret>';
        set $iyo_redirect_uri 'http://localhost:8080/_iyo/callback';

        location / {
            access_by_lua_file '/sandbox/openresty/luarocks/share/lua/5.1/iyo-login.lua';
            content_by_lua '
                local jwt = require("cpp.jwt")
                local nginx = require("iyo-auth.nginx")

                local jwt_obj = jwt.decode(nginx.get_req_jwt())

                ngx.header["Content-type"] = "text/html"
                ngx.say("Welcome "..jwt_obj.payload.username.." <a href=\'/_iyo/logout\'>Logout...</a>")';
        }

        location /_iyo/callback {
            content_by_lua_file '/sandbox/openresty/luarocks/share/lua/5.1/iyo-callback.lua';
        }

        location /_iyo/logout {
            content_by_lua_file '/sandbox/openresty/luarocks/share/lua/5.1/iyo-logout.lua';
        }

    }
}
```

Only input between `<...>` need to be changed.

When you try to access [http://localhost:8080](http://localhost:8080), you will be redirected to itsyou.online first for login.

In the previous config, `resolver` and `lua_ssl*` directives are required by [lua-rest-http](https://github.com/ledgetech/lua-resty-http) to resolve and do http requests, and the variable `$session_secret` need to be set for [lua-resty-session](https://github.com/bungle/lua-resty-session) to securly deal with cookies.

Other variables that start with `$iyo_` are needed by [lua-resty-iyo-auth](https://github.com/threefoldtech/lua-resty-iyo-auth):

* $iyo_organization: the organization name/client id, the user will be checked if he is a member of this organization.
* $iyo_secret: client secret
* $iyo_redirect_uri: a callback url that iyo will redirect to after successful login.

As you can see, we are using some helper lua files provided by `lua-resty-iyo-auth` to deal with the oauth flow for us, we only need to handle things after `access_by_lua_file` is done, in this example, we defined `content_by_lua` to be executed in case `access_by_lua_file` succeeded:

```lua
    local jwt = require("cpp.jwt")
    local nginx = require("iyo-auth.nginx")

    local jwt_obj = jwt.decode(nginx.get_req_jwt())

    ngx.header["Content-type"] = "text/html"
    ngx.say("Welcome "..jwt_obj.payload.username.." <a href=\'/_iyo/logout\'>Logout...</a>")';
```

`get_req_jwt()` is provided to get the jwt token from current request or cookies, then we use `decode()` to get user info (we don't need to do any verification, it should be done already by `lua-resty-iyo-auth`).

