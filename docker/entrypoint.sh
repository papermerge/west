#!/bin/sh

exec_server() {
  exec poetry run task server --port 8001
}

case $1 in
  server)
    exec_server
    ;;
  *)
    exec "$@"
    ;;
esac
