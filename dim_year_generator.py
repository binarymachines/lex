#!/usr/bin/env python


# generator for year dimension table

def line_array_generator(**kwargs):
    year = 2000
    id = 0
    while id < 100:
        year_value = year + id
        yield [id + 1, year_value, str(year_value) ]
        id += 1