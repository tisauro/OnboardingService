### Todo:
- implement key management
- sort out docker container


## alembic commands:

Full documentation can be found in [here](https://alembic.sqlalchemy.org/en/latest/):

- init script to be run only once: ```alembic init alembic``` as part of the configuration we change the alembic.ini
  file
  specifying the file template name as: ```file_template = %%(epoch)s_%%(slug)s```

- create a migration script: ```alembic revision --autogenerate -m "create account table"```
- running migration: ```alembic upgrade head```
- partial revision identifier: ```alembic upgrade ae1``` only part of the revision no can be specified as far as it is
  enough to identify a specific revision.
- relative migration identifiers: ```alembic upgrade +2```
- getting information: ```alembic current``` and ```alembic history --verbose```
- downgrading: ```alembic downgrade base``` base is a keyword to downgrade to the beginning otherwise
  run ```alembic downgrade revision_no```