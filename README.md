# Precocite

Installation:

docker run --name mysql -d -e MYSQL_RANDOM_ROOT_PASSWORD=yes \
    -e MYSQL_DATABASE=microblog -e MYSQL_USER=microblog \
    -e MYSQL_PASSWORD=$MYSQL_PASSWORD \
    mysql/mysql-server:5.7

docker pull rajeshmohan1991/microblog

docker run --name microblog -d -p 8000:5000 --rm -e SECRET_KEY=$SECRET_KEY \
    -e MAIL_SERVER=$MAIL_SERVER -e MAIL_PORT=587 -e MAIL_USE_TLS=true \
    -e MAIL_USERNAME=$MAIL_USERNAME -e MAIL_PASSWORD=$MAIL_PASSWORD \
    --link mysql:dbserver \
    -e DATABASE_URL=mysql+pymysql://microblog:MYSQL_PASSWORD@dbserver/microblog \
    microblog:latest
