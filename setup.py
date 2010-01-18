"""Implementation of a Pygments Lexer for the Objective-J language."""

from setuptools import setup

__author__ = 'Fish Software, Inc., 280 North, Inc.'

setup(
    name='Objective-J Pygments Lexer',
    version='1.0',
    description=__doc__,
    author=__author__,
    packages=['objjpygments'],
    entry_points='''
    [pygments.lexers]
    ObjectiveJ = objjpygments:ObjectiveJLexer
    '''
)
