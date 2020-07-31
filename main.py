#!/usr/bin/env python3

import os
import logging
import json
import logging.handlers as handlers
from pathlib import Path
import boto3
from dotenv import load_dotenv


class BackupMigration():
    def __init__(self, **kwargs):
        self.logger = Logger(level='INFO')
        self.logger.log(msg='Starting...')
        self.EMAIL = '--DL_HSDP_Biogen (at) philips.com--'
        self.logger.log(level='WARN',
                        msg='READ ME: You must email the logs to {email} upon completion'.format(email=self.EMAIL))
        self.source = {}
        self.destination = {}
        self.objects = {}
        self.completed_objects = []
        self.home = str(Path.home())
        self.get_configs()
        self.get_clients()
        self.list_objects()
        self.save_object_list()
        self.copy_objects()

        self.logger.log(level='DEBUG', msg='Leaving BackupMigration.__init__()')

    def __del__(self):
        self.logger.log(level='DEBUG', msg='Entering BackupMigration.__del__()')
        msg = 'Log File Created at: {file}; This Log file must be emailed to HSDP for validation: {email}'
        self.logger.log(level='WARN', msg=msg.format(file=self.logger.file, email=self.EMAIL))

        self.logger.log(msg='Completed...')
        self.logger.log(level='DEBUG', msg='Leaving BackupMigration.__del__()')

    def get_configs(self, **kwargs):
        self.logger.log(level='DEBUG', msg='Entering BackupMigration.get_configs()')

        load_dotenv()
        msg = 'Required variable missing; Refer to README for .env attributes; Attr: {attr}, Key: {key}, Value: {value}'

        # Load and check source bucket
        self.source['access_key'] = os.environ.get('source_access_key', kwargs.get('source_access_key', None))
        self.source['secret_key'] = os.environ.get('source_secret_key', kwargs.get('source_secret_key', None))
        self.source['bucket_name'] = os.environ.get('source_bucket_name', kwargs.get('source_bucket_name', None))
        self.source['region'] = os.environ.get('source_region', kwargs.get('source_region', None))
        for key, value in self.source.items():
            if not value:
                self.logger.log(level='ERROR', msg=msg.format(attr='source', key=key, value=value))
                raise NameError(msg.format(attr='source', key=key, value=value))

        # Load and check destination bucket
        self.destination['access_key'] = os.environ.get('destination_access_key',
                                                        kwargs.get('destination_access_key', None))
        self.destination['secret_key'] = os.environ.get('destination_secret_key',
                                                        kwargs.get('destination_secret_key', None))
        self.destination['bucket_name'] = os.environ.get('destination_bucket_name',
                                                         kwargs.get('destination_bucket_name', None))
        self.destination['region'] = os.environ.get('destination_region', kwargs.get('destination_region', None))
        for key, value in self.source.items():
            if not value:
                self.logger.log(level='ERROR', msg=msg.format(attr='source', key=key, value=value))
                raise NameError(msg.format(attr='source', key=key, value=value))

        # Validate the regions are the same
        if str(self.source['region']).split('-')[0] != str(self.destination['region']).split('-')[0]:
            msg = 'PHI data needs to within geographical region; Source: {source}, Destination: {destination}'
            self.logger.log(level='ERROR',
                            msg=msg.format(source=self.source['region'], destination=self.destination['region']))
            raise IndexError(msg.format(source=self.source['region'], destination=self.destination['region']))

        msg = 'Required attribute was not found; Attribute: {attribute}, Value: {value}'

        self.debug = os.environ.get('debug', kwargs.get('debug', False))

        self.logger.log(level='DEBUG', msg='Leaving BackupMigration.get_configs()')

    def get_clients(self):
        self.logger.log(level='DEBUG', msg='Entering BackupMigration.get_clients()')
        self.logger.log(msg='Getting Source S3 Client')
        session = boto3.Session(aws_access_key_id=self.source['access_key'],
                                aws_secret_access_key=self.source['secret_key'],
                                region_name=self.source['region'])
        self.source_client = session.client('s3')
        self.logger.log(msg='Acquired Source S3 Client')

        self.logger.log(msg='Getting Destination S3 Client')
        session = boto3.Session(aws_access_key_id=self.destination['access_key'],
                                aws_secret_access_key=self.destination['secret_key'],
                                region_name=self.destination['region'])
        self.destination_client = session.client('s3')
        self.logger.log(msg='Acquired Destination S3 Client')
        self.logger.log(level='DEBUG', msg='Leaving BackupMigration.get_clients()')

    def list_objects(self):
        self.logger.log(level='DEBUG', msg='Entering BackupMigration.list_objects()')
        paginator = self.source_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=self.source['bucket_name']):
            if 'Contents' in page:
                for object in page['Contents']:
                    if self.debug:
                        self.logger.log(level='DEBUG', msg='Key: {key}; MD5: {md5}'.format(key=object['Key'], md5=str(
                            object['ETag']).replace('"', '')))
                    self.objects[object['Key']] = str(object['ETag']).replace('"', '')
            else:
                self.logger.log(level='WARN', msg='There Was No Contents Returned: {page}'.format(page=page))
        if self.debug:
            self.logger.log(level='DEBUG', msg="Objects:\n{}".format(json.dumps(self.objects, indent=4)))

        self.logger.log(msg='Objects Discovered: {}'.format(len(self.objects)))
        self.logger.log(level='DEBUG', msg='Leaving BackupMigration.list_objects()')

    def save_object_list(self):
        self.logger.log(level='DEBUG', msg='Entering BackupMigration.save_object_list()')
        Path(os.path.join('.', 'runtime')).mkdir(parents=True, exist_ok=True)
        self.completed_objects_file = os.path.join('.', 'runtime', 'completed_objects.lst')
        self.logger.log(msg='Reading Previously Completed Objects List from: {completed_objects_file}'.format(
            completed_objects_file=self.completed_objects_file))
        if os.path.exists(self.completed_objects_file):

            with open(self.completed_objects_file, 'r') as completed_objects:
                for line in completed_objects.readlines():
                    key = str(line).strip()
                    if key:
                        self.completed_objects.append(key)
                completed_objects.close()
            self.logger.log(msg='Previously Completed Objects WERE Found: {}'.format(len(self.completed_objects)))
        else:
            self.logger.log(msg='NO Previously Completed Objects Found')

        self.logger.log(level='DEBUG', msg='Leaving BackupMigration.save_object_list()')

    def copy_objects(self):
        self.logger.log(level='DEBUG', msg='Entering BackupMigration.copy_objects()')
        Path(os.path.join('.', 'runtime')).mkdir(parents=True, exist_ok=True)
        for key, md5 in self.objects.items():
            completed_objects_file = open(self.completed_objects_file, 'a')

            if key in self.completed_objects:
                self.logger.log(level='WARN', msg='Skipping Object Already Copied: {}'.format(key))
            else:
                self.logger.log(msg="Reading Object; Bucket: {bucket}; Key: {key}; MD5: {md5}".format(
                    bucket=self.source['bucket_name'], key=key, md5=md5))

                response = self.source_client.get_object(Bucket=self.source['bucket_name'], Key=key)
                if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                    etag = str(response['ETag'])
                    clean_etag = etag.replace('"', '')

                    if md5 == clean_etag:
                        self.logger.log(level='DEBUG',
                                        msg="Object Read Success; {bucket}; Key: {key}; MD5: {md5}".format(
                                            bucket=self.source['bucket_name'], key=key, md5=clean_etag))
                    else:
                        msg = 'MD5 signatures do not match; Source: {source}; Memory: {memory}'
                        self.logger.log(level='ERROR', msg=msg.format(source=md5, memory=clean_etag))
                        raise ValueError(msg.format(source=md5, memory=clean_etag))
                else:
                    msg = "Unable to Read Object; Bucket: {bucket}; Key: {key}; MD5: {md5}"
                    self.logger.log(level='ERROR',
                                    msg=msg.format(bucket=self.source['bucket_name'], key=key, md5=clean_etag))
                    raise ValueError(msg.format(bucket=self.source['bucket_name'], key=key, md5=clean_etag))

                body = response['Body'].read()
                target = '{}'.format(key)
                self.logger.log(level='DEBUG',
                                msg="Writing Object; Bucket: {}; Key: {}".format(self.destination['bucket_name'],
                                                                                 target))
                response = self.destination_client.put_object(
                    Bucket=self.destination['bucket_name'],
                    Key=target,
                    Body=body)
                self.logger.log(msg="Wrote Object; Bucket: {bucket}; Key: {key}; MD5: {md5}".format(
                    bucket=self.destination['bucket_name'], key=target, md5=str(response['ETag']).replace('"', '')))
                completed_objects_file.write('{key}\n'.format(key=key))

        self.logger.log(level='DEBUG', msg='Leaving BackupMigration.copy_objects()')


class Logger:
    def __init__(self, **kwargs):
        self.app = str(kwargs.get('app', 'hsdp')).strip().upper()
        self.logger = logging.getLogger(self.app)
        if (self.logger.hasHandlers()):
            self.logger.handlers.clear()
        Path(os.path.join('.', 'log')).mkdir(parents=True, exist_ok=True)
        self.file = str(kwargs.get('file', os.path.join('.', 'log', '{}.log'.format(str(self.app).lower()))))

        file_handler = handlers.RotatingFileHandler(self.file, maxBytes=10000000, backupCount=1)

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.WARN)

        self.LEVELS = {'DEBUG': 10, 'INFO': 20, 'WARN': 30, 'ERROR': 40, 'CRITICAL': 50}
        level = str(kwargs.get('level', 'WARN')).strip().upper()
        if level not in self.LEVELS.keys():
            level = 'DEBUG'
        self.level = self.LEVELS[level]

        self.logger.setLevel(self.level)
        file_handler.setLevel(logging.DEBUG)

        log_formatter = logging.Formatter('%(asctime)s; %(name)s; %(levelname)s; %(message)s')
        file_handler.setFormatter(log_formatter)
        stream_handler.setFormatter(log_formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(stream_handler)

    def log(self, **kwargs):
        level = str(kwargs.get('level', 'INFO')).strip().upper()
        if level not in self.LEVELS.keys():
            level = 'WARN'
        level = self.LEVELS[level]
        msg = kwargs.get('msg', '<>')
        self.logger.log(level, msg)


def main():
    backup_migration = BackupMigration()


if __name__ == '__main__':
    main()
