from db import db

from models import House, Person, Point
db.create_tables([House, Person, Point])
House.get_or_create(name="gryffindor")
House.get_or_create(name="ravenclaw")
House.get_or_create(name="hufflepuff")
House.get_or_create(name="slytherin")
House.get_or_create(name="unknown")

houses = [i.name for i in House.select()]

print houses