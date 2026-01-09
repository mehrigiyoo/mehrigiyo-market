.PHONY: start

start: 
	systemctl restart mehrigiyo.service
	systemctl restart mehrigiyo-daphne.service
	systemctl restart mehrigiyo-celery.service

worker:
	systemctl stop mehrigiyo-celery.service
	./.env/bin/celery -A config purge
	systemctl start mehrigiyo-celery.service

backend:
	systemctl restart mehrigiyo.service

service:
	systemctl restart mehrigiyo.service

socket:
	systemctl restart mehrigiyo-daphne.service

mig:
	python3 manage.py makemigrations
	python3 manage.py migrate

install:
	pip3 install -r requirements.txt

req:
	pip3 freeze > requirements.txt
