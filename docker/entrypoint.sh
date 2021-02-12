#!/bin/bash

PGID=${PGID:-0}
[[ "$PGID" != 0 ]] &&
	addgroup \
		--gid "$PGID" \
		abc

PUID=${PUID:-0}
[[ "$PUID" != 0 ]] &&
	adduser \
		--uid "$PUID" \
		--gid "$PGID" \
		--gecos "" \
		--home /conf \
		--no-create-home \
		--disabled-password \
		abc

[[ -d "/conf" ]] || mkdir "/conf"
[[ -d "/data" ]] || mkdir "/data"

chown -R "$PUID:$PGID" /conf /data
chmod -R 755 /conf /data

if [[ ! -f "/conf/blemqtt.yml" ]]; then
	echo "Missing config file."
	echo "Pass -v ./blemqtt.yml:/conf/blemqtt.yml to your docker cmdl"
	exit 255
fi

cat <<EOF
******************************************************************
If this container fails with some error like
    'org.freedesktop.DBus.Error.AccessDenied'
try adding --privileged and -v /var/run/dbus:/var/run/dbus options
******************************************************************

EOF

exec sudo -u "$(id -n -u "$PUID")" -n \
	/usr/bin/tini -s /usr/local/bin/blemqtt -- -c "/conf/blemqtt.yml"
