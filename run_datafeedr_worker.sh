#!/bin/bash
celery -A pricehunter worker -Q datafeedr -n datafeedr.1 -l INFO --max-tasks-per-child=1
