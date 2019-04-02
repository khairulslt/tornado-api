import tornado.web
import tornado.log
import tornado.options
import sqlite3
import logging
import json
import time
from tornado.httpclient import AsyncHTTPClient

class App(tornado.web.Application):

    def __init__(self, handlers, **kwargs):
        super().__init__(handlers, **kwargs)

        # Initialising db connection
        self.db = sqlite3.connect("listings.db")
        self.db.row_factory = sqlite3.Row
        self.init_db()

    def init_db(self):
        cursor = self.db.cursor()

        # Create table
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS 'listings' ("
            + "id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,"
            + "user_id INTEGER NOT NULL,"
            + "listing_type TEXT NOT NULL,"
            + "price INTEGER NOT NULL,"
            + "created_at INTEGER NOT NULL,"
            + "updated_at INTEGER NOT NULL"
            + ");"
        )
        self.db.commit()

class BaseHandler(tornado.web.RequestHandler):
    def write_json(self, obj, status_code=200):
        self.set_header("Content-Type", "application/json")
        self.set_status(status_code)
        self.write(json.dumps((obj), indent=4))

# /public-api/listings
class PublicListings(BaseHandler):
    @tornado.gen.coroutine
    def get(self):
        http_client = AsyncHTTPClient()
        # Parsing user_id param
        user_id = self.get_argument("user_id", None)
        if user_id is not None:
            try:
                user_id = int(user_id)
            except:
                self.write_json({"result": False, "errors": "invalid user_id"}, status_code=400)
                return

        # Pull data from /listings API
        listings_response = yield http_client.fetch("http://localhost:6555/listings")
        listings_API = json.loads(listings_response.body)
        listings = listings_API["listings"]

        # Pull data from /users API
        user_response = yield http_client.fetch("http://localhost:6524/users")
        users_API = json.loads(user_response.body)
        users = users_API["users"]

        
        # display listings from /listings with merged users from /users
        '''
        Assumptions:
        For every property listing in /listings endpoint,
        there is a corresponding user_id in /users.
        '''
        for i in range(len(listings)):
            try:
                user_id_no = listings[i].pop("user_id")
                listings[i]["user"] = users[-user_id_no]
            except IndexError:
                logging.exception("user ID does not exist")
                self.write_json({"result": False, "errors": "invalid user_id"}, status_code=400)
                return None

        # Adding user_id filter clause if param is specified 
        if user_id is not None:
            user_id = int(user_id)
            listings = listings[-(user_id)]

        self.write_json({"result": True, "listings": listings})

    @tornado.gen.coroutine
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        # Validating inputs
        errors = []
        user_id_val = self._validate_user_id(data['user_id'], errors)
        listing_type_val = self._validate_listing_type(data['listing_type'], errors)
        price_val = self._validate_price(data['price'], errors)

        # End if we have any validation errors
        if len(errors) > 0:
            self.write_json({"result": False, "errors": errors}, status_code=400)
            return

        http_client = tornado.httpclient.HTTPClient()
        response = requests.post("http://localhost:6555/listings", data=data)
        self.write_json(data)

    def _validate_user_id(self, user_id, errors):
        try:
            user_id = int(user_id)
            return user_id
        except Exception as e:
            logging.exception("Error while converting user_id to int: {}".format(user_id))
            errors.append("invalid user_id")
            return None

    def _validate_listing_type(self, listing_type, errors):
        if listing_type not in {"rent", "sale"}:
            errors.append("invalid listing_type. Supported values: 'rent', 'sale'")
            return None
        else:
            return listing_type

    def _validate_price(self, price, errors):
        # Convert string to int
        try:
            price = int(price)
        except Exception as e:
            logging.exception("Error while converting price to int: {}".format(price))
            errors.append("invalid price. Must be an integer")
            return None

        if price < 1:
            errors.append("price must be greater than 0")
            return None
        else:
            return price

# /public-api/users
# only POST required



# /public-api/ping
class PingHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        self.write("pong!")

def make_app(options):
    return App([
        (r"/public-api/ping", PingHandler),
        (r"/public-api/listings", PublicListings),
        #(r"/public-api/users", PublicUsers),
    ], debug=options.debug)

if __name__ == "__main__":
    # Define settings/options for the web app
    # Specify the port number to start the web app on (default value is port 6000)
    tornado.options.define("port", default=6000)
    # Specify whether the app should run in debug mode
    # Debug mode restarts the app automatically on file changes
    tornado.options.define("debug", default=True)

    # Read settings/options from command line
    tornado.options.parse_command_line()

    # Access the settings defined
    options = tornado.options.options

    # Create web app
    app = make_app(options)
    app.listen(options.port)
    logging.info("Starting listing service. PORT: {}, DEBUG: {}".format(options.port, options.debug))

    # Start event loop
    tornado.ioloop.IOLoop.instance().start()