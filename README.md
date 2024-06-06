# Hera Admin Panel and Web Service

## Getting up and running

#### Get API Secrets from another dev

```
hera-api $ touch web/hera/secrets.py
# paste the secrets you get into this file
```

#### Create Volume for Temporary Database

```
hera-api $ docker volume create heradb-vol
```

#### Run local server

```
hera-api $ docker compose up --build
```

Browsable API docs is now available at your localhost [http://127.0.0.1:8000/api_docs/redoc/](http://127.0.0.1:8000/api_docs/redoc/).
You can also play around with the APIs, for example by visiting [User Profiles API](http://127.0.0.1:8000/user_profiles/).

#### Run database migration

```
hera-api $ docker compose run web python manage.py migrate
```

#### (Optional) Connect to your database

If you are using TablePlus app, go to Connection > New > Import from URL and paste the following:

```
postgresql://herauser:herapassword@127.0.0.1/heradb?statusColor=F8F8F8&enviroment=local&name=Docker%20PG&tLSMode=0&usePrivateKey=false&safeModeLevel=0&advancedSafeModeLevel=0
```

#### (Optional) Open browsable API documentation


#### Run Django administration commands

Prefix `docker compose run web` to your usual Django commands.

```
# django-admin example
docker compose run web django-admin startapp api

# manage.py example to create superuser to login to admin panel
docker compose run web python manage.py createsuperuser
```


## Python Development Routines

### Pip

#### Adding dependencies

```
hera-api $ cd web
hera-api/web $ pipenv install your-new-library;
hera-api/web $ pipenv lock --requirements > requirements.txt
hera-api/web $ docker compose up --build; # make sure to add --build flag to update docker image
```
**Important**

1. If you are trying to install a new library using: `pipenv install your-new-library`. You may encounter the following warning:
```
Warning: Python [some_version] was not found on your system...
Neither 'pyenv' nor 'asdf' could be found to install Python.
You can specify specific versions of Python with:
$ pipenv --python path/to/python
```
In this case, you must install the required Python version using one of the environment managers like Miniconda or others.


2. In case the command: `pipenv lock --requirements > requirements.txt` is not working you can use the following command:
```
pipenv requirements > requirements.txt
```

### Testing

#### Running unit tests

```
# You need docker compose up to get PostgreSQL running as it's used for test database 
hera-api $ docker compose up [--build] # --build only if you have modified requirements.txt

# Run tests as many times as you like:
hera-api $ docker compose run web python manage.py test
```

#### Deleting all data

```
hera-api $ docker compose run web python manage.py flush
```

### i18n

#### Generating strings file

Run in your local computer with GNU Gettext installed:

```bash
docker-compose run web django-admin makemessages -l tr -l ar
```

This will generate the the `django.po` files. Translate them and do test the compilation with

```bash
docker-compose run web django-admin compilemessages
```

However, by default, `.mo` (compiled messages) files are ignored by `.gitignore`. Therefore, for the deployment, we have to run `copilot svc exec`, then
``django-admin compilemessages`.


### Code Style

For code style guidelines, please read [CONTRIBUTING.md](CONTRIBUTING.md).

## Database Schema

![This is the database schema](docs/assets/entity-diagram.svg)


# Django Two-Factor Authentication

It is required to run migration for 2FA to work.

```
docker compose run web python manage.py migrate
```

To enable 2FA for admin,

1. Visit `account/login/`
2. Login admin, then will lead to `account/two_factor/`
3. Enable the 2FA and setup the authenticator such as Authy
4. Then can visit the admin page at `admin/`


# Deploying

1. Install Docker Desktop on Mac (or equivalents on Windows / Linux). This is pre-requisite for AWS copilot builds.
2. Install AWS copilot CLI: https://aws.github.io/copilot-cli/docs/overview/
3. Run `copilot deploy`. You will be asked which environment (test vs production-turkey) in the CLI. During this stage, docker will build an image from whatever files you have in your computer - so make sure you are in the right git branch and have the right values in settings.py and secrets.py.

