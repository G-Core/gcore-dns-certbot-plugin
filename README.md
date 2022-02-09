## G-Core DNS Authenticator plugin for Certbot

### How to develop plugin in docker
```bash
docker-compose run --rm --service-ports dev bash
pip install -e .
touch ./gcore.ini # add g-core dns api credentials

# check pylint
pylint --rcfile=.pylintrc ./certbot_dns_gcore/

certbot certonly --authenticator dns-gcore --dns-gcore-credentials=./gcore.ini -d 'example.com'
```

### Renew and check docs in docker

```bash
docker-compose run --rm --service-ports dev bash
cd ./docs
make html
cat ./_build/html/index.html
```
