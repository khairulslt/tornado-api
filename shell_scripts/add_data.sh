#!/usr/bin/env sh

# cd to root directory
cd ..

# POST to /listings 
curl http://localhost:6555/listings -XPOST \
    -d user_id=1 \
    -d listing_type=rent \
    -d price=2500 &&

curl http://localhost:6555/listings -XPOST \
    -d user_id=2 \
    -d listing_type=sale \
    -d price=5500 &&


# POST to /users
curl http://localhost:6524/users -XPOST \
    -d name="Suresh Subramaniam" &&

curl http://localhost:6524/users -XPOST \
    -d name="Michael Cheng" &&


# POST to /public-api/listings
curl -d '{"user_id": "3", "listing_type": "rent", "price": 2000}' \
    -H "Content-Type: application/json" \
    -X POST http://localhost:6111/public-api/listings &&

curl -d '{"user_id": "4", "listing_type": "sale", "price": 6700}' \
    -H "Content-Type: application/json" \
    -X POST http://localhost:6111/public-api/listings &&


# POST to /public-api/users
curl -d '{"name": "Lorel Ipsum"}' \
    -H "Content-Type: application/json" \
    -X POST http://localhost:6111/public-api/users &&

curl -d '{"name": "Ahmad Zainadi"}' \
    -H "Content-Type: application/json" \
    -X POST http://localhost:6111/public-api/users
