# MSPT Backup Migration
## Purpose
The intent of this application is to simplify the migration of in-region S3 bucket objects between heterogeneous AWS Accounts

## Assumtions
* General familiarity with python3, AWS S3, cli

## Requirements
There needs to be a ./.env file with the following attributes:
```.env
# Key for backups directory in source bucket
source_key=
clinic_name=

# source_* values are for the source bucket
source_access_key=
source_secret_key=
source_bucket_name=
source_region=us-

# destination_* values are for the destination bucket
destination_access_key=
destination_secret_key=
destination_bucket_name=
destination_region=
```
Where:
* `source_key` is AWS S3 key; The "directory-like" hierarchy
* `clinic_name` is a string used to create a new base-key in the destination bucket.


## Invocation
NOTE: Examples are from a linux/bash shell
1.  Clone this repository, then cd to it, checkout appropriate tag:
```bash
$ > git clone git@github.com:hsdp-smulford/mspt-backup-migration.git
$ > cd mspt-backup-migration
$ > git checkout v1.0.0
```
2. Create and populate the `.env` file:
```bash
$ > cp .env.tmpl .env
$ > vi .env
```
3. Source the appropriate python interpreter (`runtime.txt`) and install pkgs:
```bash
$ > cat runtime.txt
python-3.8.0
$ > python3 -m venv .venv
$ > pip install -r requirements.txt
$ > . .venv/bin/activate
(.venv) $ > pip install -r requirements.txt
(.venv) $ >
```
4. Run the migration script:
```bash
(.venv) $ > chmod +x ./main.py
(.venv) $ > ./main.py
```
5. Final step, there will be a log message indicating where the log file is and where to email it:
```log
2020-04-01 14:35:45,300; HSDP; WARNING; Log File Created at: ****; This Log file must be emailed to HSDP for validation: -**** (at) ****--
```