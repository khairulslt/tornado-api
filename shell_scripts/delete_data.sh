#!/usr/bin/env sh

# cd to root directory
cd ..

# remove databases...
# NOTE: NEVER DO THIS IN PRODUCTION, USE TRASH ... RM REMOVES DATABASE FILES ENTIRELY
# SEE: https://www.codesandnotes.com/tools-and-workflow/use-trash-instead-of-rm/
rm -f listings.db && rm -f users.db


