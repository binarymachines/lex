#!/usr/bin/env python

# generate records for month dimension table

months = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December'
]


def line_array_generator(**kwargs):    
    id = 1
    for month in months:
        yield [id, id, f"'{month}'"]
        id += 1