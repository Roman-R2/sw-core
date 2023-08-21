include .env
export

check-code:
	isort src/
	flake8 --extend-ignore E501,F401 src/

makemigrations:
	alembic revision --autogenerate


