# this file contains sensitive information like django secret key
# edit this according to your requirement
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Django_Secrets:
    def __init__(self):
        self.key = 'django-insecure-lo6zwe^$8qfdme5v&zeg3le(4ps+54b7*frt8uon+jhj6#=q=e'


class Server_Url:
    def __init__(self):
        self.allowed_hosts = ["*","192.168.5.1" 'localhost']



class Allowed_origins:
    def __init__(self):
        self.allowed_origins = ['http://localhost:8083']



class Database_configs:
    def __init__(self):
        self.test = DATABASES
        self.live = DATABASES


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'Point_of_Sale_DB',
        'USER': 'postgres',
        'PASSWORD': 'c011en89',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


