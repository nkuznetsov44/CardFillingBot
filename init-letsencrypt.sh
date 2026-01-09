#!/bin/bash

set -e

DOMAIN="cardfillingbot.nkuznetsov.com"
EMAIL="nkuznetsov44@gmail.com"
STAGING=0

if [ -d "./certbot/conf/live/$DOMAIN" ]; then
  read -p "Existing certificate found for $DOMAIN. Continue and replace? (y/N) " decision
  if [ "$decision" != "Y" ] && [ "$decision" != "y" ]; then
    exit
  fi
fi

echo "### Creating dummy certificate for $DOMAIN ..."
path="/etc/letsencrypt/live/$DOMAIN"
mkdir -p "./certbot/conf/live/$DOMAIN"
docker compose run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:4096 -days 1\
    -keyout '$path/privkey.pem' \
    -out '$path/fullchain.pem' \
    -subj '/CN=localhost'" certbot
echo

echo "### Starting nginx with HTTP-only config..."
rm -f ./nginx/conf.d/default.conf
cp ./nginx/conf.d/cardfillingbot-http.conf ./nginx/conf.d/default.conf
docker compose up --force-recreate -d nginx
echo

echo "### Deleting dummy certificate for $DOMAIN ..."
docker compose run --rm --entrypoint "\
  rm -rf /etc/letsencrypt/live/$DOMAIN && \
  rm -rf /etc/letsencrypt/archive/$DOMAIN && \
  rm -rf /etc/letsencrypt/renewal/$DOMAIN.conf" certbot
echo

echo "### Requesting Let's Encrypt certificate for $DOMAIN ..."
domain_args="-d $DOMAIN"
case "$STAGING" in
  1) staging_arg="--staging" ;;
  *) staging_arg="" ;;
esac

docker compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $staging_arg \
    $domain_args \
    --email $EMAIL \
    --rsa-key-size 4096 \
    --agree-tos \
    --force-renewal \
    --non-interactive" certbot
echo

echo "### Switching to HTTPS configuration..."
rm -f ./nginx/conf.d/default.conf
cp ./nginx/conf.d/cardfillingbot.conf ./nginx/conf.d/default.conf
echo

echo "### Reloading nginx ..."
docker compose exec nginx nginx -s reload
echo

echo "### Starting certbot service for auto-renewal..."
docker compose up -d certbot
echo

echo "### Done! Your site should now be accessible via HTTPS."
