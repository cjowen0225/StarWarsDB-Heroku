# StarWarsDB

This is a Star Wars Database that uses the swapi.tech/api to create an interactive database for both the casual and veteran Star Wars fans. This app was created using HTML (Jinja templates), CSS, SQL (SQLAlchemy and PSQL), Javascript and Python (Flask and WTForms). The database allows for creating an account to save favorites and add personal notes to the favorited items. It features categories that allow the user to narrow down the list of items as well as a search bar that will take a partial or full match to return items in a selected category. 

Please review the Design Doc to see a full list of technology used and routes on the app. 

This app can be viewed by visiting: http://owen-starwarsdb.herokuapp.com/

NOTE: While the film routes have not be deactivated for direct access, all links within the webpage to the film category have been removed. The public API uses a rate limiting feature that causing the page to timeout when attempting to reach the film routes in the app.
