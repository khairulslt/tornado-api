import tornado.web
import tornado.log
import tornado.options
import sqlite3
import logging
import json
import time

class App(tornado.web.Application):

    def __init__(self, handlers, **kwargs):
        super().__init__(handlers, **kwargs)

        # Initialising db connection
        self.db = sqlite3.connect("users.db")
        self.db.row_factory = sqlite3.Row
        self.init_db()

    def init_db(self):
        cursor = self.db.cursor()

        # Create table
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS 'USERS' ("
            + "id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,"
            + "name TEXT NOT NULL,"
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

# /users
class UsersHandler(BaseHandler):
    @tornado.gen.coroutine
    def get(self):
        # Parsing pagination params
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

        # Building select statement
        select_stmt = "SELECT * FROM users"
        # Order by and pagination
        limit = page_size
        offset = (page_num - 1) * page_size
        select_stmt += " ORDER BY created_at DESC LIMIT ? OFFSET ?"

        # Fetching users from db
        args = (limit, offset)  
        cursor = self.application.db.cursor()
        results = cursor.execute(select_stmt, args)

        users = []
        for row in results:
            fields = ["id", "name", "created_at", "updated_at"]
            user = {
                field: row[field] for field in fields
            }
            users.append(user)

        self.write_json({"result": True, "users": users})

    @tornado.gen.coroutine
    def post(self):
        # Collecting required params
        name = self.get_argument("name")
        # Validating inputs
        errors = []
        name_val = self._validate_name(name, errors)
        time_now = int(time.time() * 1e6) # Converting current time to microseconds

        # End if we have any validation errors
        if len(errors) > 0:
            self.write_json({"result": False, "errors": errors}, status_code=400)
            return
            
        # Proceed to store the users in our db
        cursor = self.application.db.cursor()
        cursor.execute(
            "INSERT INTO 'users' "
            + "('name', 'created_at', 'updated_at') "
            + "VALUES (?, ?, ?)",
            (name_val, time_now, time_now)
        )
        self.application.db.commit()

        # Error out if we fail to retrieve the newly created user
        if cursor.lastrowid is None:
            self.write_json({"result": False, "errors": ["Error while adding user to db"]}, status_code=500)
            return

        user = dict(
            id=cursor.lastrowid,
            name=name_val,
            created_at=time_now,
            updated_at=time_now
        )

        self.write_json({"result": True, "user": user})

    def _validate_name(self, name, errors):
        try:
            name = str(name)
            return name
        except Exception as e:
            logging.exception("Error while converting name to str: {}".format(name))
            errors.append("invalid name")
            return None

# /users/id
class UserIDHandler(BaseHandler):
    def get(self, id):
        # Parsing pagination params
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

        select_stmt = "SELECT * FROM users WHERE id = {}".format(id)

        # Order by and pagination
        limit = page_size
        offset = (page_num - 1) * page_size
        select_stmt += " ORDER BY created_at DESC LIMIT ? OFFSET ?"

        # Fetching users from db
        args = (limit, offset)  
        cursor = self.application.db.cursor()
        results = cursor.execute(select_stmt, args)
        user = []
        for row in results:
            fields = ["id", "name", "created_at", "updated_at"]
            user_info = {
                field: row[field] for field in fields
            }
            user.append(user_info)

        # throw error if id does not exist
        try:
            self.write_json({"result": True, "user": user_info})
        except:
            logging.exception("id does not exist: {}".format(id))
            self.write_json({"result": False, "errors": "id does not exist"}, status_code=400)
            return

# /users/ping
class PingHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        self.write("pong!")

def make_app(options):
    return App([
        (r"/users/ping", PingHandler),
        (r"/users", UsersHandler),
        (r"/users/([0-9]+)", UserIDHandler),
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
    logging.info("Starting user service. PORT: {}, DEBUG: {}".format(options.port, options.debug))

    # Start event loop
    tornado.ioloop.IOLoop.instance().start()
