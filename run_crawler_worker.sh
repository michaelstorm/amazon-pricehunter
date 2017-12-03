#!/bin/bash
celery -A pricehunter worker --concurrency=1 -Q crawler -n crawler.1 -l INFO --max-tasks-per-child=1
