#!/bin/bash
ACTION=$1

if [ "$ACTION" = "app" ]; then
    echo "Running app..."
    /usr/local/bin/run
elif [ "$ACTION" = "build_media" ]; then
    echo "Building media..."
    /usr/local/bin/build_media
elif [ "$ACTION" = "migrate" ]; then
    echo "Running migrations..."
    /usr/local/bin/run_migrations
elif [ "$ACTION" = "rebuild_index" ]; then
    echo "Rebuilding search index..."
    /usr/local/bin/rebuild_index
elif [ "$ACTION" = "update_index" ]; then
    echo "Updating search index..."
    /usr/local/bin/update_index
elif [ "$ACTION" = "master_worker" ]; then
    echo "Running master worker..."
    /usr/local/bin/master-worker
elif [ "$ACTION" = "feed_worker" ]; then
    echo "Running feed worker..."
    /usr/local/bin/feed-worker
elif [ "$ACTION" = "worker" ]; then
    echo "Running worker..."
    /usr/local/bin/worker
elif [ "$ACTION" = "update_translations" ]; then
    echo "Updating translations..."
    /usr/local/bin/update_translations
elif [ "$ACTION" = "shell" ]; then
    echo "Running shell..."
    /bin/bash -l
else
    echo "Unknown action: $ACTION"
    exit 1
fi

