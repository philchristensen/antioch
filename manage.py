#!/usr/bin/env python

# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "antioch.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
