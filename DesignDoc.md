##Star Wars DB Design Doc


									1. Introduction
### **1.1 Goals**
* Database of everything in the Star Wars Universe
	* Any Star wars character, planet, vehicle, spaceship, and species from seven Star Wars movies will be organized in a searchable database
	* They will be organized by category but also able to be searched
* The ability to create a profile and login
* The ability to save/favorite items in the database to easily access and view for personal use
* Possibly the ability to add notes to favorited items

### **1.2 Purpose**
* The goal of this website is to provide easily found data on everything Star Wars. The ability to create a profile and save items will make access specific data even easier. While this is great for just the casual fan it could be even better for someone wanting to use the information for their own project. By favoriting data and adding notes to the saved data, it would be much easier to use that data to create a separate project with the data.

										2. Data

### **2.1 Database Schema**
* Users: id, email, username, image_url, password
* Favorites: id, category, data (JSON), comments

### **2.2 External API**
* https://swapi.dev/api 
	* This API was taken down and the below API is now used
* https://www.swapi.tech/api
	* This API uses Rate Slowing and Limiting
	* This causes some slow movement between Routes especially the Film pages. These are very, very slow to move through.

### **2.2 Routes**
* /signup
* /login
* /logout
* / - Home Route
* /users/<int:user_id> - User Profile
* /users/favorite/<int:favorite_id>/update - Update a Favorite's Notes
* /users/favorite/<int:favorite_id>/delete - Delete a Favorite
* /users/profile - Update the User's profile
* /users/delete - Delete a User
* /search - Search for an Item
* /categories - Show all Data Categories
* /categories/people - Show all/searched people
* /categories/people/person - Show a specific person or add to favorites
* /categories/films - Show all/searched films
* /categories/films/film - Show a specific film or add to favorites
* /categories/planets - Show all/searched planets
* /categories/planets/planet - Show a specific planet or add to favorites
* /categories/species - Show all/searched species
* /categories/species/specie - Show a specific specie or add to favorites
* /categories/starships - Show all/searched starships
* /categories/starships/starship - Show a specific starship or add to favorites
* /categories/vehicles - Show all/searched vehicles
* /categories/vehicles/vehicle - Show a specific vehicle or add to favorites

### **2.3 Tech Stack**
* HTML,CSS (Jinja Templates)
* SQL: SQLAlchemy, bcrypt, auth
* Javascript: JQuery, JSON
* Python: Flask, Form Validation, WTForms

										3. UX 
										
### **3.1 Layout**
* Every Page
	* Nav Bar with Links to Home, Signup/Profile, Login/Logout, Categories and a Search Form
* Home Page (No User) 
	* Welcome Prompt with Signup, Login, and Categories Buttons
* Home Page (User Logged in)
	* A Welcome back prompt with User Image, Profile, Logout, and Categories Buttons
* Signup - WTForm
* Login - WTForm
* Edit Profile - WTForm
* User Profile
	* User Image, Edit and Delete Profile buttons and a list of favorites with links
* Categoroes
	* Buttons for each of the 6 data categories
* List Pages
	* A list of all items in the selected category
* Info Pages
	* All Data for the selected item
	* If logged in, there is a link to the User Profile and an Add Favorite button
	* If the Item is a favorite there is a Notes box and a button to add/update the notes or delete the favorite


### **3.2 Security Features**
* Bcrypt is used to Hash password
* Authorization is used to access favorites and edit profile
