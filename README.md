# Timing71 orchestration utilities

## Included tools

- `livetiming-directory`: manages a list of running services and their
  manifests.
- `livetiming-dvr`: Records timing and analysis data to create replay files.

Both of these are designed to be run within the context of a Crossbar router,
but can also run in standalone mode. Only one directory process should exist per
master router.

- `livetiming-rectool`: Utility for inspecting and manipulating replay files.
- `livetiming-scheduler`: Stops and starts services according to a Google
  calendar schedule.
- `livetiming-service-manager`: Stops and starts services manually.

## Included configuration

In the `crossbar/` directory are two example config files plus a simple
authentication mechanism that requires services to know a shared secret in
order to publish.

## Configuration

In addition to the configuration detailed in `livetiming-core`:

### DVR variables

- `LIVETIMING_RECORDINGS_DIR` - Directory to store completed, published
  recordings. This should also be web-accessible
- `LIVETIMING_RECORDINGS_TEMP_DIR` - Directory to store in-progress recording
  files
