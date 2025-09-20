echo '------- Build compose -------'
docker-compose up --build -d
echo '------- Start with tests -------'
docker-compose exec solver-contact-api-develop pytest --cov=app --cov-report=term-missing -vv ./tests/test.py
