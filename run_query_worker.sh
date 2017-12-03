#!/bin/bash
celery -A pricehunter worker --concurrency=1 -Q celery -l INFO --max-tasks-per-child=1 -n $*
