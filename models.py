#-*- coding: utf-8 -*-

from db import db
from peewee import *
from playhouse.sqlite_ext import *
import datetime as dt
import uuid
from playhouse.shortcuts import model_to_dict, dict_to_model
import json

###### MODELS #####

class BaseModel(Model):
    """Base model class. All descendants share the same database."""
    id = AutoField(primary_key=True)
    created_at = DateTimeField(default=dt.datetime.now)

    def __str__(self):
        return json.dumps({str(self.__class__.__name__): model_to_dict(self)},indent=4, sort_keys=True, default=str)
    def __unicode__(self):
        return str(self)
    
    class Meta:
        database = db

class House(BaseModel):
    name = CharField(max_length=80, unique=True)

class Person(BaseModel):
    name = CharField()
    slack_id = CharField(unique=True)
    house = ForeignKeyField(House)

class Point(BaseModel):
    house = ForeignKeyField(House)
    receive = ForeignKeyField(Person)
    give = ForeignKeyField(Person)
    

