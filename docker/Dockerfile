# docker run \
#	--rm -it \
#	--privileged \
#	-v /var/run/dbus:/var/run/dbus \
#	-v $PWD/conf.yml:/conf/blemqtt.yml
#	zepol/blemqtt

FROM debian
MAINTAINER luis@cuarentaydos.com
ENV DEBIAN_FRONTEND=noninteractive

# Install stuff
RUN apt-get update && \
	apt-get install --no-install-recommends -y \
		git python3 python3-pip python3-setuptools python3-wheel git tini sudo \
		gcc python3-dev pkg-config libcairo2-dev libdbus-1-dev libgirepository1.0-dev
RUN python3 -m pip install git+https://github.com/ldotlopez/blemqtt.git#egg=blemqtt pyyaml voluptuous

# Cleanup
RUN find /var/cache/apt/ -name '*.bin' -delete
RUN find /var/cache/apt/ -name '*.deb' -delete
RUN find /var/lib/apt/lists/ -type f -delete
RUN rm -r /root/.cache/pip/

# Configure entrypoint
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
