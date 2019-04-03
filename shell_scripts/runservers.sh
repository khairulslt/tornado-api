#!/usr/bin/env sh

# cd to root directory
cd ..

# serve user_service (http://localhost:6524/users)
start python user_service.py --port=6524 --debug=true

# serve listing_service (http://localhost:6555/listings)
start python listing_service.py --port=6555 --debug=true

# serve public_api (http://localhost:6111/public-api/listings)
start python public_api.py --port=6111 --debug=true

