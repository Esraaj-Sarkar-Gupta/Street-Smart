#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 13 15:10:17 2024

@author: tsampi
"""
import matplotlib.pyplot as plt
import numpy as np
import math
import time as tm
import os

filepath = "./streetsmart_data.txt"

try:
    os.makedirs('./Logs')
except:
    pass

T = tm.localtime()
filename = f"Logs/Logs_{T[7]}_{T[3]}-{T[4]}-{T[5]}.txt" # Set log file name

def log_display(text):
    with open(filename , 'a') as log_file:
        log_file.write(f"\n{T[7]} - {T[3]}:{T[4]}:{T[5]} > {text}\n")
    print(f"{T[3]}:{T[4]}:{T[5]} > {text}")
    
def haversine(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(math.sqrt(a)) 

    # Radius of Earth in meters
    r = 6371 * 1000

    return c * r
def mag(x,y,z):
    return np.sqrt(x**2 + y**2 + z**2)
with open(filepath , 'r') as data_file:
   datapoints = data_file.readlines()
   data_file.close()

file_size = os.path.getsize(filepath)

log_display(f"File of size {file_size/1024} KB has been read.")
    
#datapoints = ["L:1.2,2.1,4003;A:3.2,392.2,32.0,3234;","L:31.3,42.4,232;A:21.3,23.3,324.6,99483;"]
datatypes = [point.split(';') for point in datapoints]
#print(datatypes)
locations = []
accelerations_crude = []
for data_point in datatypes:
    locations.append(data_point[0].split(':')[1])
    accelerations_crude.append(data_point[1].split(':')[1])
    
log_display("Data points extracted")
    
#print(locations,accelerations)

accelerations = accelerations_crude # Correction function will be implimented later

index = -1  # Start before the list begins
lat = 500 # Impossible values -> denote starting positon 
long = 500 

invalid_points = 0
AMAX_errors = 0
valid_data = []
for i in range(len(datapoints)):
    #if locations[i][]
    if locations[i].split(',')[2] == '-1': # Ignore invalid data points
        index += 1
        invalid_points += 1
        #print(f"continue because {i} is {locations[i].split(',')[2]}")
        continue
    
    if float(locations[i].split(',')[0]) != lat or float(locations[i].split(',')[1]) != long: # Check for a change in coordinates
        #print(locations[i].split(',')[0] , lat)
        #delta_lat = locations[i].split(',')[0] - lat # Detmerine distance traveled 
        #delta_long = locations[i].split(',')[1] - long
        lat = float(locations[i].split(',')[0]) # Update cursor position
        long = float(locations[i].split(',')[1])
        #print(f"Updated {lat} and {long}")
        
        delta_d = haversine(float(locations[i].split(',')[0]) , float(locations[i].split(',')[1]) , float(locations[index].split(',')[0]) , float(locations[index].split(',')[1]))
        
        delta_t = float(locations[i].split(',')[2]) - float(locations[index].split(',')[2]) # Determine time taken
        #print(delta_d , delta_t)

        max_a = 0  # Define max acc variable
        # AMAX loop
        for j in range(index , i + 1):
            a_x = float(accelerations[j].split(',')[0])
            a_y = float(accelerations[j].split(',')[1])
            a_z = float(accelerations[j].split(',')[2])
                
            mag_a = mag(a_x , a_y , a_z) # Magnitude of acceleration
            
            if mag_a >= max_a: # Check for maximum 
                max_a = mag_a
            else:
                pass
            
            # Check for errors
            if float(accelerations[j].split(',')[3]) > float(locations[index].split(',')[2]) and float(accelerations[j].split(',')[3] < locations[i].split(',')[2]):
                pass
                #log_display("No Errors in AMAX ")
            else:
                AMAX_errors += 1
                log_display(f"Errors in AMAX: data points outside defined time range. Expected L_INDEX: {locations[index].split(',')[2]} < A_NOW {accelerations[j].split(',')[3]} < L_I: {locations[i].split(',')[2]}")
                # Include checks for major errors in time discrepency 
        #print(max_a)
        valid_data.append([locations[i].split(',')[0] , locations[i].split(',')[1] , delta_d , delta_t , max_a])
        index = i
    else:
        continue
    
print(valid_data[1:]) # First element will be incorrect 



valid_data.pop(0) # First element will contain errors due to randomly assigned initial values - removed

latitudes = []
longitudes = []

for n in range(len(valid_data)):
    latitudes.append(valid_data[n][0])
    longitudes.append(valid_data[n][1])
    
plt.figure(figsize=(10,10))
plt.title("Coordinates")   
plt.scatter(latitudes , longitudes , color = 'green')

plt.xlabel("Latitude")
plt.ylabel("Longitude")

plt.show()

plt.figure(figsize = (10,10))
