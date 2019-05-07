# Individual Notes

```bash
# all commands run on Windows Git Bash, could have compatibility issues on other OS
# to use shell_scripts for faster initialization
cd shell_scripts

# start running all servers 
sh runservers.sh

# add data with POST
sh add_data.sh

# remove databases (!IMPORTANT, ONLY RUN WHEN SURE... CANNOT UNDO => SEE NOTE INSIDE delete_data.sh ON USING TRASH INSTEAD)
# ensure all database connections are closed before running command
sh delete_data.sh
```

## Running Tests

```bash
# pip install tavern
# first, ensure no db connections are open, then run sh delete_data.sh
# start running all servers 
sh runservers.sh

# add data with POST
sh add_data.sh

# cd tests
# run tavern tests
py.test test_apis.tavern.yaml -vv
```

## On Attempting Tornado Testing

- My first attempt at unit testing a REST api (I first tried using the standard tornado unittesting docs but I ran into a lot of compatibility issues on Windows)

- Tavern currently does not [support setUp/tearDown methods](https://github.com/taverntesting/tavern/pull/115)

- to compensate for this, I figured using shell scripts to mimick setup/teardown methods might work... probably not a scalable idea, a bad one at that

- Using tavern is probably not the best way to do it since there is no support for unit testing asynchronous code

- Using built in [tornado testing](https://www.tornadoweb.org/en/stable/testing.html) with something like nose is probably the best way to do it

## On Using Windows

- tweaked commands a little bit for Windows

```bash
# Locate the path for the Python 3 installation
Get-Command python 

# Start the virtual environment
.\env\Scripts\activate
```

---

# A Tornado Server
Writing non-blocking/asynchronous code with Tornado

## Setup
We will be using Python 3 for this exercise.

### Install pip
pip is a handy tool to install libraries/dependencies for your python programs. pip should already come installed on your system. Head over to https://pip.pypa.io/en/stable/installing/ for steps to install pip if it's not available.

### Install virtualenv
We use virtualenv to create an isolated running environment to install dependencies and launch the web application. Head over to https://virtualenv.pypa.io/en/stable/installation/ for instructions to install virtualenv.

### Install dependencies
Once you have pip and virtualenv set up, we can proceed to create the environment to run our web applications:

```bash
# Locate the path for the Python 3 installation
which python3

# Create the virtual environment in a folder named "env" in the current directory
virtualenv env --python=<path_to_python_3>

# Start the virtual environment
source env/bin/activate

# Install the required dependencies/libraries
pip install -r python-libs.txt
```
You'll see `(env)` show up at the beginning of the command line if you've started virtual environment successfully. To check if the dependencies are installed correctly, run `pip freeze` and check if the output looks something like this:

```
backports-abc==0.4
tornado==4.4.2
```

### Run the listing service
Now we're all set to run the listing service!

```bash
# Run the listing service
python listing_service.py --port=6000 --debug=true
```
The following settings that can be configured via command-line arguments when starting the app:

- `port`: The port number to run the application on (default: `6000`)
- `debug`: Runs the application in debug mode. Applications running in debug mode will automatically reload in response to file changes. (default: `true`)

### Create listings
Time to add some data into the listing service!

```bash
curl localhost:8888/listings -XPOST \
    -d user_id=1 \
    -d listing_type=rent \
    -d price=4500
```
