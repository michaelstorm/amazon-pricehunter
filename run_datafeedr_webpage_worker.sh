#!/bin/bash
celery -A pricehunter worker --concurrency=1 -Q datafeedr_webpages -n datafeedr_webpages.1 -l WARNING --max-tasks-per-child=1
