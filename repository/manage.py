#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import pathlib


def main():
    """Run administrative tasks."""
    # Allow importing sibling projects located at the workspace root (e.g. ../scheduling)
    # by adding the workspace root to sys.path. This makes absolute imports like
    # `scheduling.common.serializer_fields` work when running this project's manage.py.
    workspace_root = str(pathlib.Path(__file__).resolve().parents[1])
    if workspace_root not in sys.path:
        sys.path.insert(0, workspace_root)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'repository.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
