import os

from flask import Flask, render_template, request, flash, redirect, session, g, abort
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

import requests
from forms import UserAddForm, UserEditForm, LoginForm
from models import db, connect_db, User, Favorite

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.

# Update and uncomment
app.config['SQLALCHEMY_DATABASE_URI'] = (
   os.environ.get('DATABASE_URL', 'postgres://zoimfqpeppybzg:a8ecb249775bca39b6b71511d44b79119371c049126456a64b5ea202a4acbda3@ec2-34-205-209-14.compute-1.amazonaws.com:5432/dbb7m0iln0490v'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "nevertell")
toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout



@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
        # set_user(app, User.query.get(session[CURR_USER_KEY]))

    else:
        g.user = None
        # set_user(app, None)


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError as e:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    flash("You have successfully logged out.", 'success')
    return redirect("/login")


##############################################################################

# General Routes

@app.route("/")
def homepage():

    if not g.user:
        return render_template('home-anon.html')

    user = g.user
    return render_template('home.html', user=user)

@app.errorhandler(404)
def page_not_found(e):
    """404 NOT FOUND page."""

    return render_template('404.html'), 404

##############################################################################

# User Routes

@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    favorites = (Favorite
                .query
                .filter(Favorite.user_id == user_id)
                .order_by(Favorite.id.desc())
                .all())
        
    return render_template('users/show.html', user=user, favorites=favorites)


"""@app.route('/users/favorite/add', methods=['GET','POST'])
def add_favorite():
    Add a favorite for the currently-logged-in user.

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    url = request.args.get('url')
    category = request.args.get('category')
    data = request.args.get('data')

    fav = Favorite(category=category, data=data)
    g.user.favorites.append(fav)
    db.session.commit()
    
    return redirect(url)"""


@app.route('/users/favorite/<int:favorite_id>/update', methods=['GET','POST'])
def update_favorite(favorite_id):
    """Update a favorite for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    comments = request.args.get('comments')
    url = request.args.get('url')
    Fav = Favorite.query.get_or_404(favorite_id)

    Fav.comments = comments

    db.session.commit()

    return redirect(url)
    
@app.route('/users/favorite/<int:favorite_id>/delete', methods=['GET','POST'])
def delete_favorite(favorite_id):
    """Delete a Favorite."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    url = request.args.get('url')
    fav = Favorite.query.get_or_404(favorite_id)
    if fav.user_id != g.user.id:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    db.session.delete(fav)
    db.session.commit()

    return redirect(url)

@app.route('/users/profile', methods=["GET", "POST"])
def edit_profile():
    """Update profile for current user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = g.user
    form = UserEditForm(obj=user)

    if form.validate_on_submit():
        if User.authenticate(user.username, form.password.data):
            user.username = form.username.data
            user.email = form.email.data
            user.image_url = form.image_url.data or "/static/images/default-pic.png"

            db.session.commit()
            return redirect(f"/users/{user.id}")

        flash("Wrong password, please try again.", 'danger')

    return render_template('users/edit.html', form=form, user_id=user.id)


@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")

##############################################################################

# Database Item Routes

@app.route('/search', methods=['GET', 'POST'])
def handle_search():
    """Direct the search to the correct route"""

    cat = request.args.get('cat')
    search = request.args.get('search')
    if cat == "people" :
        return redirect(f'/categories/people?search={search}')
    elif cat == "films" :
        return redirect(f'/categories/films?search={search}')
    elif cat == "planets" :
        return redirect(f'/categories/planets?search={search}')
    elif cat == "species" :
        return redirect(f'/categories/species?search={search}')
    elif cat == "starships" :
        return redirect(f'/categories/starships?search={search}')
    elif cat == "vehicles" :
        return redirect(f'/categories/vehicles?search={search}')    

@app.route('/categories')
def show_categories():
    """Show the categories in the Database"""

    return render_template('data/categories.html')

@app.route('/categories/people', methods=['GET','POST'])
def show_people():
    """List people in the database"""

    search = request.args.get('search')
    people_data = []
    search_data = 0
    

    if search :
        URL = f'https://www.swapi.tech/api/people/?name={search}'
        search_data = requests.get(URL).json()
        search_data = search_data['result']
        print(search_data)
    else :
        URL = "https://www.swapi.tech/api/people/"
        while URL != None :
            response = requests.get(URL).json()
            for person in response['results'] :
                people_data.append(person)
            URL = response['next']
        
    
    return render_template("data/list_people.html", people_data=people_data, search_data=search_data)

@app.route('/categories/people/person', methods=['GET','POST'])
def show_person():
    """Show data for a person in the database"""

    data = request.args.get('data')
    p_data = requests.get(data).json()
    p_data = p_data['result']['properties']
    person_data = {}
    for key, value in p_data.items() :
        person_data[key] = value.capitalize()
    # species_data = requests.get(person_data["species"][0]).json() if len(person_data["species"]) > 0 else "N/A"

    fav = Favorite(category='People', data=person_data)
    if request.args.get('fav') == "add" :
        g.user.favorites.append(fav)
        db.session.commit()
        print('Hello World')
              
        return redirect(f"/categories/people/person?data={data}&added=true")

    planet_data = requests.get(person_data["homeworld"]).json()
    
    isFavorite = None
    favId = None
    favComments = None

    if not g.user:
        user = None
    else:
        user = g.user
        for fav in g.user.favorites :
            if fav.category == "People" :
                if fav.data['name'] == person_data['name'] :
                    isFavorite = 1
                    favId = fav.id
                    favComments = fav.comments
                    break

    if request.args.get('updated') == 'true' :
        flash(f"Notes Successfully Updated!", "success")
    
    if request.args.get('added') == 'true' :
        flash(f"Favorite Successfully Added!", "success")

    if request.args.get('deleted') == 'true' :
        flash(f"Favorite Deleted!", "danger")

    
    return render_template("data/person.html", person_data=person_data, planet_data=planet_data, user=user, isFavorite=isFavorite, favId=favId, favComments=favComments) 


''' The Films route will timeout because the Free public API cannot handle the size of the request'''
@app.route('/categories/films', methods=['GET','POST'])
def show_films():
    """List films in the database"""
    
    search = request.args.get('search')
    films_data = []
    search_data = 0
    

    if search :
        URL = f'https://www.swapi.tech/api/films/?search={search}'
        films_data = requests.get(URL).json()
        films_data = films_data['result']
    else :
        URL = "https://www.swapi.tech/api/films/"
        films_data = requests.get(URL).json()
        films_data = films_data['result']
                
    
    return render_template("data/list_films.html", films_data=films_data)

@app.route('/categories/films/film', methods=['GET','POST'])
def show_film():
    """Show data for a film in the database"""

    data = request.args.get('data')
    film_data = requests.get(data).json()
    film_data = film_data['result']['properties']

    fav = Favorite(category='Films', data=film_data)
    if request.args.get('fav') == "add" :
        g.user.favorites.append(fav)
        db.session.commit()
        
        return redirect(f"/categories/films/film?data={data}")

    people_data = []
    if len(film_data["characters"]) > 0 :
       for person in film_data["characters"] :
           people_data.append(requests.get(person).json())
    else :
       people_data.append("N/A")

    species_data = []
    if len(film_data["species"]) > 0 :
       for species in film_data["species"] :
           species_data.append(requests.get(species).json())
    else :
       species_data.append("N/A")

    planets_data = []
    if len(film_data["planets"]) > 0 :
       for planet in film_data["planets"] :
           planets_data.append(requests.get(planet).json())
    else :
       planets_data.append("N/A")

    vehicles_data = []
    if len(film_data["vehicles"]) > 0 :
       for vehicle in film_data["vehicles"] :
           vehicles_data.append(requests.get(vehicle).json())
    else :
       vehicles_data.append("N/A")

    starships_data = []
    if len(film_data["starships"]) > 0 :
       for starship in film_data["starships"] :
           starships_data.append(requests.get(starship).json())
    else :
       starships_data.append("N/A")

    
    isFavorite = None
    favId = None
    favComments = None

    if not g.user:
        user = None
    else:
        user = g.user
        for fav in g.user.favorites :
            if fav.category == "Films" :
                if fav.data['title'] == film_data['title'] :
                    isFavorite = 1
                    favId = fav.id
                    favComments = fav.comments
                    break

    if request.args.get('updated') == 'true' :
        flash(f"Notes Successfully Updated!", "success")
    
    if request.args.get('added') == 'true' :
        flash(f"Favorite Successfully Added!", "success")

    if request.args.get('deleted') == 'true' :
        flash(f"Favorite Deleted!", "danger")

    return render_template("data/film.html", film_data=film_data, people_data=people_data, species_data=species_data, planets_data=planets_data, vehicles_data=vehicles_data, starships_data=starships_data, user=user, isFavorite=isFavorite, favId=favId, favComments=favComments)

@app.route('/categories/planets')
def show_planets():
    """List planets in the database"""

    search = request.args.get('search')
    planets_data = []
    search_data = 0
    
    if search :
        URL = f'https://www.swapi.tech/api/planets/?search={search}'
        search_data = requests.get(URL).json()
        search_data = search_data['result']
    else :
        URL = "https://www.swapi.tech/api/planets/"
        while URL != None :
            response = requests.get(URL).json()
            for planet in response['results'] :
                planets_data.append(planet)
            URL = response['next']

    return render_template("data/list_planets.html", planets_data=planets_data, search_data=search_data)

@app.route('/categories/planets/planet', methods=['GET','POST'])
def show_planet():
    """Show data for a planet in the database"""

    data = request.args.get('data')
    p_data = requests.get(data).json()
    p_data = p_data['result']['properties']
    planet_data = {}
    for key, value in p_data.items() :
        planet_data[key] = value.capitalize()

    fav = Favorite(category='Planets', data=planet_data)
    if request.args.get('fav') == "add" :
        g.user.favorites.append(fav)
        db.session.commit()
        
        return redirect(f"/categories/planets/planet?data={data}")

    isFavorite = None
    favId = None
    favComments = None

    if not g.user:
        user = None
    else:
        user = g.user
        for fav in g.user.favorites :
            if fav.category == "Planets" :
                if fav.data['name'] == planet_data['name'] :
                    isFavorite = 1
                    favId = fav.id
                    favComments = fav.comments
                    break

    return render_template("data/planet.html", planet_data=planet_data, user=user, isFavorite=isFavorite, favId=favId, favComments=favComments)

@app.route('/categories/species')
def show_species():
    """List species in the database"""

    search = request.args.get('search')
    species_data = []
    search_data = 0
    
    if search :
        URL = f'https://www.swapi.tech/api/species/?search={search}'
        search_data = requests.get(URL).json()
        search_data = search_data['result']
    else :
        URL = "https://www.swapi.tech/api/species/"
        while URL != None :
            response = requests.get(URL).json()
            for specie in response['results'] :
                species_data.append(specie)
            URL = response['next']

    if request.args.get('updated') == 'true' :
        flash(f"Notes Successfully Updated!", "success")
    
    if request.args.get('added') == 'true' :
        flash(f"Favorite Successfully Added!", "success")

    if request.args.get('deleted') == 'true' :
        flash(f"Favorite Deleted!", "danger")

    return render_template("data/list_species.html", species_data=species_data, search_data=search_data)


@app.route('/categories/species/specie', methods=['GET','POST'])
def show_specie():
    """Show data for a specie in the database"""

    data = request.args.get('data')
    s_data = requests.get(data).json()
    s_data = s_data['result']['properties']
    specie_data = {}
    for key, value in s_data.items() :
        if type(value) is not list :
            specie_data[key] = value.capitalize()
        else :
            specie_data[key] = value

    fav = Favorite(category='Species', data=specie_data)
    if request.args.get('fav') == "add" :
        g.user.favorites.append(fav)
        db.session.commit()

        return redirect(f"/categories/species/specie?data={data}")


    people_data = []
    if len(specie_data["people"]) > 0 :
       for person in specie_data["people"] :
           people_data.append(requests.get(person).json())
    else :
       people_data.append("N/A")

    planet_data = requests.get(specie_data["homeworld"]).json()

    isFavorite = None
    favId = None
    favComments = None

    if not g.user:
        user = None
    else:
        user = g.user
        for fav in g.user.favorites :
            if fav.category == "Species" :
                if fav.data['name'] == specie_data['name'] :
                    isFavorite = 1
                    favId = fav.id
                    favComments = fav.comments
                    break

    if request.args.get('updated') == 'true' :
        flash(f"Notes Successfully Updated!", "success")
    
    if request.args.get('added') == 'true' :
        flash(f"Favorite Successfully Added!", "success")

    if request.args.get('deleted') == 'true' :
        flash(f"Favorite Deleted!", "danger")
    
    return render_template("data/specie.html", specie_data=specie_data, people_data=people_data, planet_data=planet_data, user=user, isFavorite=isFavorite, favId=favId, favComments=favComments)

@app.route('/categories/starships')
def show_starships():
    """List starships in the database"""

    search = request.args.get('search')
    starships_data = []
    search_data = 0
    
    if search :
        URL = f'https://www.swapi.tech/api/starships/?search={search}'
        search_data = requests.get(URL).json()
        search_data = search_data['result']
    else :
        URL = "https://www.swapi.tech/api/starships/"
        while URL != None :
            response = requests.get(URL).json()
            for starship in response['results'] :
                starships_data.append(starship)
            URL = response['next']

    return render_template("data/list_starships.html", starships_data=starships_data, search_data=search_data)

@app.route('/categories/starships/starship', methods=['GET','POST'])
def show_starship():
    """Show data for a starship in the database"""

    data = request.args.get('data')
    s_data = requests.get(data).json()
    s_data = s_data['result']['properties']
    starship_data = {}
    for key, value in s_data.items() :
        if type(value) is not list :
            starship_data[key] = value.capitalize()
        else :
            starship_data[key] = value

    fav = Favorite(category='Starships', data=starship_data)
    if request.args.get('fav') == "add" :
        g.user.favorites.append(fav)
        db.session.commit()

        return redirect(f"/categories/starships/starship?data={data}")

    
    people_data = []
    if len(starship_data["pilots"]) > 0 :
       for person in starship_data["pilots"] :
           people_data.append(requests.get(person).json())
    else :
       people_data.append("N/A")

    isFavorite = None
    favId = None
    favComments = None

    if not g.user:
        user = None
    else:
        user = g.user
        for fav in g.user.favorites :
            if fav.category == "Starships" :
                if fav.data['name'] == starship_data['name'] :
                    isFavorite = 1
                    favId = fav.id
                    favComments = fav.comments
                    break

    if request.args.get('updated') == 'true' :
        flash(f"Notes Successfully Updated!", "success")
    
    if request.args.get('added') == 'true' :
        flash(f"Favorite Successfully Added!", "success")

    if request.args.get('deleted') == 'true' :
        flash(f"Favorite Deleted!", "danger")

    return render_template("data/starship.html", starship_data=starship_data, people_data=people_data, user=user, isFavorite=isFavorite, favId=favId, favComments=favComments)
    
@app.route('/categories/vehicles')
def show_vehicles():
    """List vehicles in the database"""    

    search = request.args.get('search')
    vehicles_data = []
    search_data = 0
    
    if search :
        URL = f'https://www.swapi.tech/api/vehicles/?search={search}'
        search_data = requests.get(URL).json()
        search_data = search_data['result']
    else :
        URL = "https://www.swapi.tech/api/vehicles/"
        while URL != None :
            response = requests.get(URL).json()
            for vehicle in response['results'] :
                vehicles_data.append(vehicle)
            URL = response['next']

    return render_template("data/list_vehicles.html", vehicles_data=vehicles_data, search_data=search_data)

@app.route('/categories/vehicles/vehicle', methods=['GET','POST'])
def show_vehicle():
    """Show data for a vehicle in the database"""

    data = request.args.get('data')
    v_data = requests.get(data).json()
    v_data = v_data['result']['properties']
    vehicle_data = {}
    for key, value in v_data.items() :
        if type(value) is not list :
            vehicle_data[key] = value.capitalize()
        else :
            vehicle_data[key] = value

    fav = Favorite(category='Vehicles', data=vehicle_data)
    if request.args.get('fav') == "add" :
        g.user.favorites.append(fav)
        db.session.commit()

        return redirect(f"/categories/vehicles/vehicle?data={data}")

    
    people_data = []
    if len(vehicle_data["pilots"]) > 0 :
       for person in vehicle_data["pilots"] :
           people_data.append(requests.get(person).json())
    else :
       people_data.append("N/A")

    films_data = []
    if len(vehicle_data["films"]) > 0 :
       for film in vehicle_data["films"] :
           films_data.append(requests.get(film).json())
    else :
       films_data.append("N/A")   

    isFavorite = None
    favId = None
    favComments = None

    if not g.user:
        user = None
    else:
        user = g.user
        for fav in g.user.favorites :
            if fav.category == "Vehicles" :
                if fav.data['name'] == vehicle_data['name'] :
                    isFavorite = 1
                    favId = fav.id
                    favComments = fav.comments
                    break

    if request.args.get('updated') == 'true' :
        flash(f"Notes Successfully Updated!", "success")
    
    if request.args.get('added') == 'true' :
        flash(f"Favorite Successfully Added!", "success")

    if request.args.get('deleted') == 'true' :
        flash(f"Favorite Deleted!", "danger")

    return render_template("data/vehicle.html", vehicle_data=vehicle_data, people_data=people_data, films_data=films_data, user=user, isFavorite=isFavorite, favId=favId, favComments=favComments)    