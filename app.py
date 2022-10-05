#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
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
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

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


db.create_all()


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    venues = Venue.query.all()
    data = []
    cities_states = Location.query.all()
    shows = Shows.query.all()
    
    now = datetime.now()
    
    for loc in cities_states:
      venue_list = []
      for venue in venues:
        if(loc.id == venue.id):
          shows = Shows.query.filter_by(venue_id= venue.id)
          num_upcoming = 0
          if(shows.count()):
            num_upcoming = 0
          else:
            for i in shows:
              if i.start_time > now:
                num_upcoming += 1
            
          venue_list.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": num_upcoming
          })
      data.append({
            "city": loc.city,
            "state": loc.state,
            "venues": venue_list
        })
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    
    search_term = request.form.get('search_term', '')
    venues = Venue.query.filter(Venue.name.ilike('%' + search_term + '%')).all()
    venue_list = []
    now = datetime.now()
    for venue in venues:
        venue_shows = Shows.query.filter_by(venue_id=venue.id).all()
        num_upcoming = 0
        for show in venue_shows:
            if show.start_time > now:
                num_upcoming += 1

        venue_list.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": num_upcoming  # FYI, template does nothing with this
        })
    response = {
    "count": len(venues),
    "data": venue_list
    }
    
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # replace with real venue data from the venues table, using venue_id
    venue = Venue.query.filter_by(id=venue_id).one_or_none()
    if(venue is None):
      abort(404)
      
    loc = Location.query.filter_by(id=venue.location_id).one_or_none()
    
    genres = [ genre.type for genre in venue.genres_v ]
    past_shows = []
    past_shows_count = 0
    upcoming_shows = []
    upcoming_shows_count = 0
    now = datetime.now()
    for show in venue.shows:
        artist = Artist.query.filter_by(id = show.artist_id).one_or_none()
        if show.start_time > now:
            upcoming_shows_count += 1
            upcoming_shows.append({
                "artist_id": show.artist_id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": format_datetime(str(show.start_time))
            })
        if show.start_time < now:
            past_shows_count += 1
            past_shows.append({
                "artist_id": show.artist_id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": format_datetime(str(show.start_time))
            })
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": genres,
        "address": venue.address,
        "city": loc.city,
        "state": loc.state,
        "phone": venue.phone,
        "website": "https://www.themusicalhop.com",
        "facebook_link": venue.facebook_link,
        "seeking_artist": venue.seeking_artist,
        "seeking_description": "",
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": past_shows_count,
        "upcoming_shows_count": upcoming_shows_count,
    }
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form_data = request.form.to_dict()
    
    print(form_data)

    if form_data['seeking_talent'] == 'y':
      seeking_telant = True
    else:
      seeking_telant = False
    
    try:
        city = Location.query.filter_by(city=form_data['city']).one_or_none()
        if(city is None):
          city_new = Location(city=form_data['city'], state=form_data['state'])
          db.session.add(city_new)
          db.session.commit()
          city = Location.query.filter_by(city=form_data['city'])
        new_venue = Venue(name=form_data['name'], location_id=city.id, address=form_data['address'], phone=form_data['phone'], \
            seeking_artist=seeking_telant, image_link=form_data['image_link'], \
            facebook_link=form_data['facebook_link'])
        genre=form_data['genres']
        fetch_genre = Genre.query.filter_by(type=genre).one_or_none()  
        if fetch_genre:
            new_venue.genres_v.append(fetch_genre)

        else:
            new_genre = Genre(type=genre)
            db.session.add(new_genre)
            new_venue.genres_v.append(new_genre) 
        db.session.add(new_venue)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()
        abort(500)
    finally:
        flash('Venue was successfully listed!')
        db.session.close()

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    venue = Venue.query.filter_by(id=venue_id).one_or_none()
    if venue is None:
      abort(404)
    else:
      try:
        db.session.delete(venue)
        db.session.commit()
      except: 
        flash('An error occurred while deleting')
        db.session.rollback()
        abort(400)
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return jsonify({
                'deleted': True,
                'url': url_for('venues')
            })

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():    
    artists = Artist.query.order_by(Artist.name).all()
    
    # data = [{
    #     "id": 4,
    #     "name": "Guns N Petals",
    # }, {
    #     "id": 5,
    #     "name": "Matt Quevedo",
    # }, {
    #     "id": 6,
    #     "name": "The Wild Sax Band",
    # }]
    return render_template('pages/artists.html', artists=artists)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '')
    artist_list = []
    artists = Artist.query.filter(Artist.name.ilike('%' + search_term + '%')).all()

    now = datetime.now()
    for artist in artists:
        artist_shows = Shows.query.filter_by(artist_id=artist.id).all()
        num_upcoming = 0
        for show in artist_shows:
            if show.start_time > now:
                num_upcoming += 1

        artist_list.append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": num_upcoming 
        })

    response = {
        "count": len(artist_list),
        "data": artist_list
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    artist = Artist.query.filter_by(id=artist_id).one_or_none()
    if(artist is None):
      abort(404)
    genres = [ genre.type for genre in artist.genres_a ]
    loc = Location.query.filter_by(id = artist.location_id)
    
    past_shows = []
    past_shows_count = 0
    upcoming_shows = []
    upcoming_shows_count = 0
    now = datetime.now()
    for show in artist.shows:
        venue = Venue.query.filter_by(id=show.venue_id).one_or_none()
        if show.start_time > now:
            upcoming_shows_count += 1
            upcoming_shows.append({
                "venue_id": show.venue_id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": format_datetime(str(show.start_time))
            })
        if show.start_time < now:
            past_shows_count += 1
            past_shows.append({
                "venue_id": show.venue_id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": format_datetime(str(show.start_time))
            })
    
    data = {
          "id": artist.id,
          "name": artist.name,
          "genres": genres,
          "city": loc[0].city,
          "state": loc[0].state,
          "phone": artist.phone,
          "facebook_link": artist.facebook_link,
          "seeking_venue": artist.seeking_venue,
          "image_link": artist.image_link,
          "past_shows": past_shows,
          "upcoming_shows": upcoming_shows,
          "past_shows_count": past_shows_count,
          "upcoming_shows_count": upcoming_shows_count,
    }
    # data = list(filter(lambda d: d['id'] ==
    #             artist_id, [data1, data2, data3]))[0]
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  
    artist = Artist.query.filter_by(id=artist_id).one_or_none()
    form = ArtistForm(obj=artist)
    if(artist is None):
      abort(404)
    
    genres = [genre.type for genre in artist.genres_a]
    
    loc = Location.query.filter_by(id=artist.location_id).one_or_none()
    artist = {
        "id": artist.id,
        "name": artist.name,
        "genres": genres,
        "city": loc.city,
        "state": loc.state,
        "phone": artist.phone,
        "facebook_link": artist.facebook_link,
        "seeking_talent": artist.seeking_venue,
        "image_link": artist.image_link
    }
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # artist record with ID <artist_id> using the new attributes
    
    form = request.form.to_dict()
    print(form)
    try:
        artist = Artist.query.filter_by(id=artist_id).one_or_none()

        loc = Location.query.filter_by(city=form['city']).one_or_none()
        
        if loc is None:
          loc=Location(city=form['city'],state= form['state'])
          db.session.add(loc)
          db.session.commit()
          
        
        artist.name = form['name']
        artist.location_id = loc.id
        artist.phone = form['phone']
        artist.seeking_venue = True if 'seeking_venue' in  form.keys() else False
        artist.image_link = form['image_link']
        artist.facebook_link = form['facebook_link']
        
        
        artist.genres_a.clear()
        
        genre_add = Genre.query.filter_by(type=form['genres']).one_or_none()  # Throws an exception if more than one returned, returns None if none
        if genre_add is None:
            new_genre = Genre(type=form['genres'])
            db.session.add(new_genre)
            artist.genres_a.append(new_genre)
        else:
            artist.genres_a.append(genre_add)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()
        abort(404)
    finally:
        db.session.close()
    

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    
  
    venue = Venue.query.filter_by(id=venue_id).one_or_none()
    form = VenueForm(obj=venue)
    
    if(venue is None):
      abort(404)
    
    genres = [genre.type for genre in venue.genres_v]
    
    loc = Location.query.filter_by(id=venue.location_id).one_or_none()
    if loc is None:
        loc=Location(city=form['city'],state= form['state'])
        db.session.add(loc)
        db.session.commit()
    venue = {
        "id": venue_id,
        "name": venue.name,
        "genres": genres,
        "address": venue.address,
        "city": loc.city,
        "state": loc.state,
        "phone": venue.phone,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_artist,
        "image_link": venue.image_link
    }
    
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # venue record with ID <venue_id> using the new attributes
    form = request.form.to_dict()
    print(form)
    try:
        venue = Venue.query.filter_by(id=venue_id).one_or_none()

        loc = Location.query.filter_by(city=form['city']).one_or_none()
        venue.name = form['name']
        venue.location_id = loc.id
        venue.address = form['address']
        venue.phone = form['phone']
        venue.seeking_artist = True if 'seeking_talent' in form.keys() else False
        venue.image_link = form['image_link']
        venue.facebook_link = form['facebook_link']
        
        venue.genres_v.clear()
        
        
        
        genre_add = Genre.query.filter_by(type=form['genres']).one_or_none()  # Throws an exception if more than one returned, returns None if none
        if genre_add is None:
            new_genre = Genre(type=form['genres'])
            db.session.add(new_genre)
            venue.genres_v.append(new_genre)
        else:
            venue.genres_v.append(genre_add)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()
        abort(404)
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form_data = request.form.to_dict()
    
    print(form_data)

    if form_data['seeking_venue'] == 'y':
      seeking_venue = True
    else:
      seeking_venue = False
    
    try:
        city = Location.query.filter_by(city=form_data['city']).one_or_none()
        if(city is None):
          city_new = Location(city=form_data['city'], state=form_data['state'])
          db.session.add(city_new)
          db.session.commit()
          city = Location.query.filter_by(city=form_data['city'])
        new_artist = Artist(name=form_data['name'], location_id=city.id,  phone=form_data['phone'], \
            seeking_venue=seeking_venue, image_link=form_data['image_link'], \
            facebook_link=form_data['facebook_link'])
        genre =form_data['genres']
        fetch_genre = Genre.query.filter_by(type=genre).one_or_none()  
        if fetch_genre:
            new_artist.genres_a.append(fetch_genre)

        else:
            new_genre = Genre(type=genre)
            db.session.add(new_genre)
            new_artist.genres_a.append(new_genre) 
        db.session.add(new_artist)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()
        abort(500)
    finally:
        flash('Venue was successfully listed!')
        db.session.close()
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    shows = Shows.query.all()
    data=[]
    for show in shows:
      venue = Venue.query.filter_by(id=show.venue_id).one_or_none()
      artist = Artist.query.filter_by(id=show.artist_id).one_or_none()
      data.append({
        "venue_id": show.venue_id,
        "venue_name": venue.name,
        "artist_id": show.artist_id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": format_datetime(str(show.start_time))
      })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = request.form.to_dict()
    
    try:
        new_show = Shows(start_time=form['start_time'], artist_id=form['artist_id'], venue_id=form['venue_id'])
        db.session.add(new_show)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()
        abort(404)
    finally:
        db.session.close()

    # on successful db insert, flash success
    flash('Show was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
