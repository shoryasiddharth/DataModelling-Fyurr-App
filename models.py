from flask_migrate import Migrate
from forms import *
from flask_wtf import Form
from logging import Formatter, FileHandler
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_moment import Moment
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
import babel
import config
import dateutil.parser
import json
from enum import unique
from collections import UserList
import collections
import collections.abc
collections.Callable = collections.abc.Callable

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String, nullable=False)

class Location(db.Model):
    __tablename__ = 'state_city'

    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    relation_Venue = db.relationship('Venue', backref='state_city', uselist=False)
    relation_Artist = db.relationship('Artist', backref='state_city', uselist=False)


# for mamy to many relationahip
venue_genre_table = db.Table('venue_genre', db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True), db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'),  primary_key=True))
class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    seeking_artist = db.Column(db.Boolean)
    facebook_link = db.Column(db.String(120))

    # implement any missing fields, as a database migration using Flask-Migrate
    location_id = db.Column(db.Integer, db.ForeignKey('state_city.id'), unique=True)
    genres_v = db.relationship( 'Genre', secondary=venue_genre_table, backref=db.backref('Venue'))
    shows = db.relationship('Shows', backref='Venue', lazy=True)

# for mamy to many relationahip
artist_genre_table = db.Table('artist_genre',  db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'), primary_key=True), db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'),  primary_key=True))

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    phone = db.Column(db.String(120))
    # genres = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    location_id = db.Column(
        db.Integer, db.ForeignKey('state_city.id'), unique=True)
    genres_a = db.relationship(
        'Genre', secondary=artist_genre_table, backref=db.backref('Artist'))
    shows = db.relationship('Shows', backref='Artist', lazy=True)


class Shows(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.now())
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


db.create_all()