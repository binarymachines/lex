#!/usr/bin/env python

# generate records for the permit type dimension table

#  (Premise Residence, Premise Business, 
# Carry Business, Carry Guard/Security, 
# Limited Carry, 
# Gun Custodian, 
# Retired Law Enforcement Officer, 
# Special Carry, or Rifle/Shotgun permit).



p_types = [
    {'abbrev': 'PR', 'desc': 'Premise Residence'},
    {'abbrev': 'PB', 'desc': 'Premise Businesss'},
    {'abbrev': 'CB', 'desc': 'Carry Business'},
    {'abbrev': 'CG', 'desc': 'Carry Guard/Security'},
    {'abbrev': 'SC', 'desc': 'Special Carry'},
    {'abbrev': 'GC', 'desc': 'Gun Custodian'},
    {'abbrev': 'RL', 'desc': 'Retired LEO'},
    {'abbrev': 'RS', 'desc': 'Rifle/Shotgun'},
    {'abbrev': 'LC', 'desc': 'Limited Carry'},
    {'abbrev': 'SX', 'desc': 'Abbreviation Unknown'}
]

def line_array_generator(**kwargs):    
    id = 1
    for p_type in p_types:
        yield [id, f"p_type['abbrev']", f"p_type['desc']"]
        id += 1 