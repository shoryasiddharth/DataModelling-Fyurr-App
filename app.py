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
from flask import (
    Flask, 
    render_template, 
    request, 
    Response, 
    flash, 
    redirect, 
    url_for, 
    abort, 
    jsonify
)
from enum import unique
from collections import UserList
import collections
import collections.abc
collections.Callabsle = collections.abc.Callable
from models import (
    Genre, 
    Location, 
    artist_genre_table, 
    Artist, 
    Venue, 
    venue_genre_table, 
    Shows, 
    app, 
    db, 
    format_datetime)
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#


#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

db.create_all()

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
    past_shows_query = db.session.query(Shows, Artist).join(Artist).filter(Shows.venue_id==venue_id).filter(Shows.start_time<datetime.now()).all()
    past_shows = []
    for show, artist in past_shows_query:
        past_shows.append({
                "artist_id": show.venue_id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": format_datetime(str(show.start_time))
            })
        
    upcoming_shows_query = db.session.query(Shows, Artist).join(Artist).filter(Shows.venue_id==venue_id).filter(Shows.start_time>datetime.now()).all()
    upcoming_shows = []
    for show, artist in upcoming_shows_query:
        upcoming_shows.append({
                "artist_id": show.venue_id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": format_datetime(str(show.start_time))
            })
    # past_shows = []
    past_shows_count = len(past_shows_query)
    # upcoming_shows = []
    upcoming_shows_count = len(upcoming_shows_query)
    # now = datetime.now()
    
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": genres,
        "address": venue.address,
        "city": loc.city,
        "state": loc.state,
        "phone": venue.phone,
        "seeking_description": venue.seeking_description,
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
    form_data = VenueForm(request.form, meta={"csrf": False})
    
    print(form_data.genres.data)
    
    if form_data.validate():


        
        try:
            city = Location.query.filter_by(city=form_data.city.data).one_or_none()
            if(city is None):
                city_new = Location(city=form_data.city.data, state=form_data.state.data)
                db.session.add(city_new)
                db.session.commit()
            city = Location.query.filter_by(city=form_data.city.data).one_or_none()
            new_venue = Venue(name=form_data.name.data, seeking_description= form_data.seeking_description.data, location_id=city.id, address=form_data.address.data, phone=form_data.phone.data, \
                seeking_artist=form_data.seeking_talent.data, image_link=form_data.image_link.data, \
                facebook_link=form_data.facebook_link.data)
            genres=form_data.genres.data
            for genre in genres:
                fetch_genre = Genre.query.filter_by(type=genre).one_or_none()  
                if fetch_genre is not None:
                    new_venue.genres_v.append(fetch_genre)

                else:
                    new_genre = Genre(type=genre)
                    db.session.add(new_genre)
                    new_venue.genres_v.append(new_genre) 
            db.session.add(new_venue)
            db.session.commit()
            flash('Venue was successfully listed!')
        except Exception as e:
            print(e)
            db.session.rollback()
            abort(500)
        finally:
            
            db.session.close()

        return render_template('pages/home.html')
    else:
        abort(401)


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
    past_shows_query = db.session.query(Shows, Venue).join(Venue).filter(Shows.artist_id==artist_id).filter(Shows.start_time<datetime.now()).all()
    past_shows = []
    print(past_shows_query)
    for show, venue in past_shows_query:
        past_shows.append({
                "venue_id": show.venue_id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": format_datetime(str(show.start_time))
            })
        
    upcoming_shows_query = db.session.query(Shows, Venue).join(Venue).filter(Shows.artist_id==artist_id).filter(Shows.start_time>datetime.now()).all()
    upcoming_shows = []
    for show, venue in upcoming_shows_query:
        upcoming_shows.append({
                "venue_id": show.venue_id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": format_datetime(str(show.start_time))
            })
    # past_shows = []
    past_shows_count = len(past_shows_query)
    # upcoming_shows = []
    upcoming_shows_count = len(upcoming_shows_query)
    # now = datetime.now()
    # for show in artist.shows:
    #     venue = Venue.query.filter_by(id=show.venue_id).one_or_none()
    #     if show.start_time > now:
    #         upcoming_shows_count += 1
    #         upcoming_shows.append({
    #             "venue_id": show.venue_id,
    #             "venue_name": venue.name,
    #             "venue_image_link": venue.image_link,
    #             "start_time": format_datetime(str(show.start_time))
    #         })
    #     if show.start_time < now:
    #         past_shows_count += 1
    #         past_shows.append({
    #             "venue_id": show.venue_id,
    #             "venue_name": venue.name,
    #             "venue_image_link": venue.image_link,
    #             "start_time": format_datetime(str(show.start_time))
    #         })
    
    data = {
          "id": artist.id,
          "name": artist.name,
          "genres": genres,
          "city": loc[0].city,
          "state": loc[0].state,
          "phone": artist.phone,
          "facebook_link": artist.facebook_link,
          "seeking_description": artist.seeking_description,
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
        "seeking_description": artist.seeking_description,
        "phone": artist.phone,
        "facebook_link": artist.facebook_link,
        "seeking_talent": artist.seeking_venue,
        "image_link": artist.image_link
    }
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # artist record with ID <artist_id> using the new attributes
    
    form = ArtistForm(request.form, meta={"csrf": False})
    print(form)
    if form.validate():
        try:
            artist = Artist.query.filter_by(id=artist_id).one_or_none()

            loc = Location.query.filter_by(city=form.city.data).one_or_none()
            
            if loc is None:
                loc=Location(city=form.city.data ,state= form.state.data)
                db.session.add(loc)
                db.session.commit()
                
                
            artist.name = form.name.data
            artist.location_id = loc.id
            artist.phone = form.phone.data
            artist.seeking_description = form.seeking_description.data
            artist.seeking_venue = form.seeking_venue.data
            artist.image_link = form.image_link.data
            artist.facebook_link = form.facebook_link.data
            
            
            artist.genres_a.clear()
            
            for genre in form.genres.data:
                genre_add = Genre.query.filter_by(type=genre).one_or_none()  # Throws an exception if more than one returned, returns None if none
                if genre_add is None:
                    new_genre = Genre(type=genre)
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
    else:
        flash('Artist detials were not updated!')
        abort(401)


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
    form = VenueForm(request.form, meta={"csrf": False})
    print(form.seeking_talent.data)
    if form.validate():
        try:
            venue = Venue.query.filter_by(id=venue_id).one_or_none()

            loc = Location.query.filter_by(city=form.city.data).one_or_none()
            venue.name = form.name.data
            venue.location_id = loc.id
            venue.address = form.address.data
            venue.phone = form.phone.data
            venue.seeking_description: form.seeking_description.data
            venue.seeking_artist = form.seeking_talent.data
            venue.image_link = form.image_link.data
            venue.facebook_link = form.facebook_link.data
            
            venue.genres_v.clear()
            
            for genre in form.genres.data:
                genre_add = Genre.query.filter_by(type=genre).one_or_none()  # Throws an exception if more than one returned, returns None if none
                if genre_add is None:
                    new_genre = Genre(type=genre)
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
    else:
        flash('Venue was not updated!')
        abort(401)
#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form_data = ArtistForm(request.form, meta={"csrf": False})
    
    if form_data.validate():
        
        try:
            city = Location.query.filter_by(city=form_data.city.data).one_or_none()
            if(city is None):
                city_new = Location(city=form_data.city.data, state=form_data.state.data)
                db.session.add(city_new)
                db.session.commit()
            city = Location.query.filter_by(city=form_data.city.data).one_or_none()
            new_artist = Artist(name=form_data.name.data, location_id=city.id, seeking_description = form_data.seeking_description.data,  phone=form_data.phone.data, \
                seeking_venue=form_data.seeking_venue.data, image_link=form_data.image_link.data, \
                facebook_link=form_data.facebook_link.data)
            genres =form_data.genres.data
            for genre in genres:
                fetch_genre = Genre.query.filter_by(type=genre).one_or_none()  
                if fetch_genre:
                    new_artist.genres_a.append(fetch_genre)
                else:
                    new_genre = Genre(type=genre)
                    db.session.add(new_genre)
                    new_artist.genres_a.append(new_genre) 
            db.session.add(new_artist)
            db.session.commit()
            flash('Artist ' + form_data.name.data + ' was successfully listed!')
        except Exception as e:
            print(e)
            db.session.rollback()
            abort(500)
        finally:
            flash('Venue was successfully listed!')
            db.session.close()
        # on successful db insert, flash success

        return render_template('pages/home.html')
    else:
        flash('Artist was not added!')
        abort(401)

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
    form = ShowForm(request.form, meta={"csrf": False})
    if form.validate():
    
        try:
            new_show = Shows(start_time=form.start_time.data, artist_id=form.artist_id.data, venue_id=form.venue_id.data)
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
    else:
        flash('Show was not listed!')
        abort(401)


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
    port = int(os.environ.get('PORT', 6000))
    app.run(host='0.0.0.0', port=port)
'''
