FROM nginx:alpine

RUN apk update
RUN apk upgrade

RUN apk add python3 docker-cli certbot openssl
RUN mkdir -p /etc/nginx/conf.d
RUN mkdir -p /etc/letsencrypt
RUN mkdir -p /tmp/letsencrypt

COPY autoproxy.py /opt/autoproxy.py
RUN chmod +x /opt/autoproxy.py

COPY proxied.conf.tmpl /opt/proxied.conf.tmpl

COPY 10-gen-certs.sh /docker-entrypoint.d/
RUN chmod +x /docker-entrypoint.d/10-gen-certs.sh

COPY 30-autoproxy.sh /docker-entrypoint.d/
RUN chmod +x /docker-entrypoint.d/30-autoproxy.sh
