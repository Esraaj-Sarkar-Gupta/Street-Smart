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

filepath = "./Upstreetsmart_data_alpha.txt"
#filepath = './' + input("Filename: ./")

try:
    os.makedirs('./Logs') # Make log file if it doesn't exist already
except:
    pass

T = tm.localtime() # Get the local time
filename = f"Logs/Logs_{T[7]}_{T[3]}-{T[4]}-{T[5]}.txt" # Set log file name

# Important physical constants 
g = 9.80 # acceleration due to gravity

# Logging functions
def log(text):
    with open(filename , 'a') as log_file:
        log_file.write(f"\n{T[7]} - {T[3]}:{T[4]}:{T[5]} > {text}\n")
    
def log_display(text):
    with open(filename , 'a') as log_file:
        log_file.write(f"\n{T[7]} - {T[3]}:{T[4]}:{T[5]} > {text}\n")
    print(f"{T[3]}:{T[4]}:{T[5]} > {text}")
   
# Use haversine function to determin the distance between two coordinates
def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(math.sqrt(a)) 

    # Radius of Earth in meters
    r = 6371 * 1000

    return c * r # (m/s)

# Determine the magnitude of a three dimensional vector
def mag(x,y,z): 
    return np.sqrt(x**2 + y**2 + z**2)

# Function to correct acceleration values ACCORECT - THIS NEEDS FIXING
def correct_acceleration(crude_accelerations_data, tolerance):
    # Initialise data storange lists
    corrected_accelerations = []
    acceleration_times = []
    crude_accelerations = []
    
    runtime_errors = 0
    
    phi = -100
    theta = -100
    
    
    for crude_value in crude_accelerations_data:        
        crude_value_x, crude_value_y, crude_value_z = float(crude_value.split(',')[0]), float(crude_value.split(',')[1]), float(crude_value.split(',')[2]) # Unpack accelerometer data 
        acceleration_times.append(float(crude_value.split(',')[3])) # Unpack time data 
        
        magnitude = mag(crude_value_x, crude_value_y, crude_value_z)
        
        crude_accelerations.append(np.array([[crude_value_x],
                                             [crude_value_y],
                                             [crude_value_z]]))
        
        if magnitude <= g + tolerance and magnitude >= g - tolerance: # Check for resting condition            
            phi = np.arccos(crude_value_z / g)
            theta = np.arcsin(crude_value_y / (g * np.sin(phi)))
            corrected_accelerations.append(np.array([[0],
                                                     [0],
                                                     [g]]))
            
            if np.isnan(phi) or np.isnan(theta):
                runtime_errors += 1
                log(f"Encountered a runtime error where theta = {theta} and phi = {phi}")
                
            log(f"Updated orientation to theta = {theta} , phi = {phi}")
        else:
            if theta == -100 or phi == -100:
                log("Skipping acceleration correction due to invalid orientation")
                
                corrected_accelerations.append(np.array([[0],
                                                         [0],
                                                         [0]]))
                continue
            transformation_matrix = np.array([[crude_value_x, -np.sin(theta), np.cos(phi) * np.cos(theta)],
                                              [crude_value_y, np.cos(theta), np.cos(phi) * np.sin(theta)],
                                              [crude_value_z, 0, -np.sin(phi)]])
            corrected_values = transformation_matrix.T @ np.array([[crude_value_x],
                                                                   [crude_value_y],
                                                                   [crude_value_z]])
            corrected_accelerations.append(corrected_values)
    log_display(f"ACCORRECT finished with {runtime_errors} runtime errors for a total of {len(crude_acceleration_data)} datapoints. ")
    return corrected_accelerations, acceleration_times, crude_accelerations
    

# Open data file and pull contents from it into a data object
with open(filepath , 'r') as data_file:
   datapoints = data_file.readlines()
   data_file.close()

file_size = os.path.getsize(filepath) # Determine size of data file

log_display(f"File of size {file_size/1024} KB has been read.")
    
datatypes = [point.split(';') for point in datapoints] # Seperate data types from the text file object 

# Initialise lists to hold relevant data
locations = []
crude_acceleration_data = []

# Unpack data from text file objects into corresponding lists
for data_point in datatypes:
    locations.append(data_point[0].split(':')[1])
    crude_acceleration_data.append(data_point[1].split(':')[1])
    
log_display("Data points extracted")
    
accelerations, acceleration_times, crude_accelerations = correct_acceleration(crude_acceleration_data, 0.2) # Pull corrected acceleration values from function, along with useful accessory results
log_display("Acceleration values corrected")

index = -1  # Start before the list begins
lat = 500 # Impossible values -> denote starting positon 
long = 500 

# Initialise error counters and valid_data list
invalid_points = 0
AMAX_errors = 0
AMAX_warnings = 0
valid_data = []

first_time = -1 # Initialise with impossible start time

for i in range(len(datapoints)):
    if locations[i].split(',')[2] == '-1': # Ignore invalid data points
        index += 1
        invalid_points += 1
        continue
    
    if first_time == -1: # Start time is unassigned
        first_time = acceleration_times[i]
    else:
        pass # Start time has already been assigned
    
    if float(locations[i].split(',')[0]) != lat or float(locations[i].split(',')[1]) != long: # Check for a change in coordinates
        #print(locations[i].split(',')[0] , lat)
        #delta_lat = locations[i].split(',')[0] - lat # Detmerine distance traveled 
        #delta_long = locations[i].split(',')[1] - long
        lat = float(locations[i].split(',')[0]) # Update cursor position
        long = float(locations[i].split(',')[1])
        #print(f"Updated {lat} and {long}")
        
        delta_d = haversine(float(locations[i].split(',')[0]) , float(locations[i].split(',')[1]) , float(locations[index].split(',')[0]) , float(locations[index].split(',')[1]))
        
        delta_t = float(locations[i].split(',')[2]) - float(locations[index].split(',')[2]) # Determine time taken

        max_a = 0  # Define max acc variable
        # AMAX loop
        for j in range(index , i + 1):
            a_x = accelerations[j][0]
            a_y = accelerations[j][1]
            a_z = accelerations[j][2]
                
            mag_a = mag(a_x , a_y , a_z) # Magnitude of acceleration
            
            if mag_a >= max_a: # Check for maximum 
                max_a = mag_a
            else:
                pass
            
            # Check for errors

            min_time = float(locations[index].split(',')[2])
            max_time = float(locations[i].split(',')[2])
            
            # Check for discrepencies in time measurements
            if acceleration_times[j] < min_time or acceleration_times[j] > max_time:
                
                # Check for nature of discrepency
                if acceleration_times[j] < min_time: 
                    diff = min_time - acceleration_times
                elif acceleration_times[j] > max_time:
                    diff = acceleration_times[j] - max_time
                
                # Check for severity of discrepency
                if diff <= 500:
                    AMAX_warnings += 1
                    log(f"Discrepency in AMAX with diff < 0.500 seconds. Expected L_INDEX: {locations[index].split(',')[2]} < A_NOW {acceleration_times[j]} < L_I: {locations[i].split(',')[2]}. Data point discounted from resultant valid data set.")
                else:
                    AMAX_errors += 1
                    log_display(f"Severe error occured in AMAX with diff >= 0.500 seconds.Expected L_INDEX: {locations[index].split(',')[2]} < A_NOW {acceleration_times[j]} < L_I: {locations[i].split(',')[2]}  ")
                    continue           
            else:
                pass

        valid_data.append([float(locations[i].split(',')[0]) , float(locations[i].split(',')[1]) , delta_d , delta_t , max_a, (acceleration_times[j] - first_time) / 1000]) # Append processed data into valid data list
        index = i # Update index
        
    else:
        continue
    
# print(valid_data[1:]) # First element will be incorrect 
log_display(f"AMAX finished with {AMAX_errors} errors and {AMAX_warnings} minor discrepencies.")


valid_data.pop(0) # First element will contain errors due to randomly assigned initial values - removed

# Initialise data lists for various relevant data 
latitudes = []
longitudes = []
velocities = []
acceleration = []
instances = []
crude_accelerations_mag = []

# Unpack data from valid_data list into individual data lists
for n in range(len(valid_data)):
    latitudes.append(valid_data[n][0])
    longitudes.append(valid_data[n][1])
    velocities.append(valid_data[n][2] / (valid_data[n][3] / 1000)) # Time is registered in milliseconds
    acceleration.append(valid_data[n][4])
    instances.append(valid_data[n][5] / 1000)
    crude_accelerations_mag.append(np.sqrt(crude_accelerations[n][0] **2 + crude_accelerations[n][1] **2 + crude_accelerations[n][2] **2))
    
acceleration_times_second = [t / 1000 for t in acceleration_times]

# Coordinate mapping plot
plt.figure(figsize=(10,10))
plt.title(f"Coordinates: {filepath}")   
plt.scatter(latitudes , longitudes , color = 'lime')
plt.xlabel("Latitude")
plt.ylabel("Longitude")
plt.show()


# Velocity plot
plt.figure(figsize = (10,10))
plt.title(f"Variation of Velocity with time: {filepath}")
plt.plot(instances, velocities, color = 'blue', marker = "o")
plt.xlabel('Seconds from initialisation')
plt.ylabel("Velocity (m/s)")
plt.show()


# Acceleration plot
plt.figure(figsize = (10,10))
plt.title(f"Variation of acceleration with time: {filepath}")

plt.plot(instances, [float(a) for a in acceleration], color = 'red' , marker = 'o')
plt.plot(instances, crude_accelerations_mag, color = 'grey' , marker = 'o')
plt.xlabel("Time (s)")
plt.ylabel("Acceleration (m/s^2)")
plt.show() 

plt.figure(figsize = (10,10))
plt.title(f"Variation of CRUDE acceleration with time: {filepath}")

plt.plot(instances, crude_accelerations_mag, color = 'grey' , marker = 'o')
plt.xlabel("Time (s)")
plt.ylabel("Acceleration (m/s^2)")
plt.show() 

plt.figure(figsize = (10,10))
plt.title(f"Deviations due to corrected accelerations: {filepath}")


plt.scatter(acceleration_times, [a[0] for a in accelerations] , color = 'blue', marker = 'o')
#plt.scatter(acceleration_times, [a[1] for a in accelerations] , color = 'red', marker = 'o')
#plt.scatter(acceleration_times, [a[2] for a in accelerations] , color = 'green', marker = 'o')


plt.plot(acceleration_times, [a[2] for a in crude_accelerations] , color = 'black', marker = 'o')

#plt.plot(acceleration_times, accelerations, color = 'blue', marker = 'o' )
#plt.plot(acceleration_times, crude_accelerations, color = 'red' , marker = 'o')
plt.show()


log_display(f"The number of data points considered: {len(valid_data)} out of {len(datapoints)} datapoints")