# PoC Status

## This is a PoC and not meant for production usage

- The data is stored on docker volumes
- there is no data backup and recovery mechanism in place
- basic authentication has been added to allow for just two users with roles
  reader and editor

## Possible improvements

### Data management

Instead of using docker volumes, proper databases can be added, see
[server setup](install/server.md)

### Authentication

It would make sense to add a proper authentication, distinguishing between users
with the role `editor` and allowing them to upload private projects, where only
they can edit the metadata.
