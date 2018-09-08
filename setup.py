# antioch
#
#

import os

import setuptools

# disables creation of .DS_Store files inside tarballs on Mac OS X
os.environ['COPY_EXTENDED_ATTRIBUTES_DISABLE'] = 'true'
os.environ['COPYFILE_DISABLE'] = 'true'

dist = setuptools.setup(
    name               = "antioch",
    version            = "0.9",
    packages           = setuptools.find_packages(),
    author             = "Phil Christensen",
    author_email       = "phil@bubblehouse.org",
    description        = "a next-generation MUD/MOO-like virtual world engine",
    license            = "MIT",
    keywords           = "antioch moo lambdamoo mud game",
    url                = "https://github.com/philchristensen/antioch",
    long_description   = """antioch is a web application for building scalable, interactive virtual worlds.
                             Begun as a MOO-like system for building virtual worlds, antioch aims to
                             take the LambdaMOO approach to creating online worlds, and update it in hopes
                             of attracting new players to an old idea.
                         """.replace('\t', '').replace('\n', ''),
)
