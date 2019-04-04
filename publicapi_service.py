import tornado.web
import tornado.log
import tornado.options
import logging
import json
import urllib
from tornado.httpclient import AsyncHTTPClient


class BaseHandler(tornado.web.RequestHandler):
    def write_json(self, obj, status_code=200):
        self.set_header("Content-Type", "application/json")
        self.set_status(status_code)
        self.write(json.dumps((obj), indent=4))


# /public-api/listings
class PublicListings(BaseHandler):
    @tornado.gen.coroutine
    def get(self):
        page_num = self.get_argument("page_num", 1)
        page_size = self.get_argument("page_size", 10)
        try:
            page_num = int(page_num)
        except:
            logging.exception("Error while parsing page_num: {}".format(page_num))
            self.write_json({"result": False, "errors": "invalid page_num"}, status_code=400)
            return

        try:
            page_size = int(page_size)
        except:
            logging.exception("Error while parsing page_size: {}".format(page_size))
            self.write_json({"result": False, "errors": "invalid page_size"}, status_code=400)
            return

        # return generators from relevant endpoints
        listings_generator, users_generator = yield [*multiple_async_http_requests(page_num, page_size)]

        # Pull data from /listings API
        listings_API = json.loads(listings_generator.body)
        listings = listings_API.get("listings")

        # Pull data from /users API
        users_API = json.loads(users_generator.body)
        users = users_API.get("users")

        # error out if key doesn't exist
        if (listings is None) or (users is None):
            logging.exception("key error during API dict access")
            self.write_json({"result": False, "errors": "service error"}, status_code=500)
            return

        # Parsing user_id param
        user_id = self.get_argument("user_id", None)
        if user_id is not None:
            try:
                user_id = int(user_id)
            except:
                self.write_json({"result": False, "errors": "invalid user_id"}, status_code=400)
                return

        # display listings from /listings with merged users from /users
        '''
        Assumptions:
        For every property listing in /listings endpoint,
        there is a corresponding user_id in /users.
        If there is a listing with no corresponding user: throw error
        '''
        for i in range(len(listings)):
            try:
                user_id_no = listings[i].pop("user_id")
                listings[i]["user"] = users[i]
            except IndexError:
                logging.exception("check databases, every listing needs corresponding name and user_id")
                self.write_json({"result": False, "errors": "invalid user_id"}, status_code=400)
                return None

        # Adding user_id filter clause if param is specified 
        if user_id is not None:
            user_id = int(user_id)

            # follows behaviour from listing_service.py, if user_id is 0, return empty listings
            if user_id is 0:
                listings = []
            else:
                try:
                    listings = listings[-(user_id)]
                except IndexError:
                # follows behaviour from listing_service.py, if user_id does not exist, return empty listings
                    listings = []

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

        http_client = AsyncHTTPClient()
        body = urllib.parse.urlencode(data)
        response = http_client.fetch("http://localhost:6555/listings", method='POST', body=body)
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


def multiple_async_http_requests(page_num, page_size):
    http_client = AsyncHTTPClient()
    if page_num and page_size:
        listings_response = http_client.fetch("http://localhost:6555/listings?page_num={}&page_size={}".format(page_num, page_size))
        user_response = http_client.fetch("http://localhost:6524/users?page_num={}&page_size={}".format(page_num, page_size))
    elif page_num:
        listings_response = http_client.fetch("http://localhost:6555/listings?page_num={}".format(page_num))
        user_response = http_client.fetch("http://localhost:6524/users?page_num={}".format(page_num))
    elif page_size:
        listings_response = http_client.fetch("http://localhost:6555/listings?page_size={}".format(page_size))
        user_response = http_client.fetch("http://localhost:6524/users?page_size={}".format(page_size))
    # GET http_response from /listings & /users
    return listings_response, user_response


# /public-api/users
# only POST supported
class PublicUsers(BaseHandler):
    @tornado.gen.coroutine
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        # Validating inputs
        errors = []
        name_val = self._validate_name(data['name'], errors)

        # End if we have any validation errors
        if len(errors) > 0:
            self.write_json({"result": False, "errors": errors}, status_code=400)
            return

        http_client = AsyncHTTPClient()
        body = urllib.parse.urlencode(data)
        response = http_client.fetch("http://localhost:6524/users", method='POST', body=body)
        self.write_json(data)

    # assumptions: we only want strings that only have letters in them, "dan99" or 95 are not valid names
    # also allows for white spaces in case of e.g ("Daniel <space> Radcliffe")
    # validates if name is alphabetical string
    def _validate_name(self, name, errors):
        if isinstance(name, str) and name.replace(' ','').isalpha():
            return name
        else:
            logging.exception("Name is {} - should be alphabetical string".format(name))
            errors.append("invalid name")
            return None


# /public-api/ping
class PingHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        self.write("pong!")


def make_app(options):
    return tornado.web.Application([
        (r"/public-api/ping", PingHandler),
        (r"/public-api/listings", PublicListings),
        (r"/public-api/users", PublicUsers),
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
    logging.info("Starting publicapi service. PORT: {}, DEBUG: {}".format(options.port, options.debug))

    # Start event loop
    tornado.ioloop.IOLoop.instance().start()