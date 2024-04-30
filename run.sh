#!/usr/bin/env sh

while ! ./manage.py sqlflush > /dev/null 2>&1; do
  echo "Waiting for mysql..."
  sleep 2
done

python manage.py migrate --no-input
python manage.py test --no-input --failfast
python manage.py create_first_admin
#python manage.py create_base_configs
#python manage.py create_permissions
python manage.py runserver 0.0.0.0:8000 --insecure