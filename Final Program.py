import sys
sys.path.append('../')
from Common.project_library import *

# Modify the information below according to you setup and uncomment the entire section

# 1. Interface Configuration
project_identifier = 'P3B' # enter a string corresponding to P0, P2A, P2A, P3A, or P3B
ip_address = '169.254.105.124' # enter your computer's IP address
hardware = False # True when working with hardware. False when working in the simulation

# 2. Servo Table configuration
short_tower_angle = 315 # enter the value in degrees for the identification tower 
tall_tower_angle = 90 # enter the value in degrees for the classification tower
drop_tube_angle = 180#270# enter the value in degrees for the drop tube. clockwise rotation from zero degrees

# 3. Qbot Configuration
bot_camera_angle = -21.5 # angle in degrees between -21.5 and 0

# 4. Bin Configuration
# Configuration for the colors for the bins and the lines leading to those bins.
# Note: The line leading up to the bin will be the same color as the bin 

bin1_offset = 0.20 # offset in meters
bin1_color = [1,0,0] #red
bin2_offset = 0.15
bin2_color = [0,1,0] #green
bin3_offset = 0.15
bin3_color = [0,0,1] #blue
bin4_offset = 0.15
bin4_color = [1,0,1] #purple

#--------------- DO NOT modify the information below -----------------------------

if project_identifier == 'P0':
    QLabs = configure_environment(project_identifier, ip_address, hardware).QLabs
    bot = qbot(0.1,ip_address,QLabs,None,hardware)
    
elif project_identifier in ["P2A","P2B"]:
    QLabs = configure_environment(project_identifier, ip_address, hardware).QLabs
    arm = qarm(project_identifier,ip_address,QLabs,hardware)

elif project_identifier == 'P3A':
    table_configuration = [short_tower_angle,tall_tower_angle,drop_tube_angle]
    configuration_information = [table_configuration,None, None] # Configuring just the table
    QLabs = configure_environment(project_identifier, ip_address, hardware,configuration_information).QLabs
    table = servo_table(ip_address,QLabs,table_configuration,hardware)
    arm = qarm(project_identifier,ip_address,QLabs,hardware)
    
elif project_identifier == 'P3B':
    table_configuration = [short_tower_angle,tall_tower_angle,drop_tube_angle]
    qbot_configuration = [bot_camera_angle]
    bin_configuration = [[bin1_offset,bin2_offset,bin3_offset,bin4_offset],[bin1_color,bin2_color,bin3_color,bin4_color]]
    configuration_information = [table_configuration,qbot_configuration, bin_configuration]
    QLabs = configure_environment(project_identifier, ip_address, hardware,configuration_information).QLabs
    table = servo_table(ip_address,QLabs,table_configuration,hardware)
    arm = qarm(project_identifier,ip_address,QLabs,hardware)
    bins = bins(bin_configuration)
    bot = qbot(0.1,ip_address,QLabs,bins,hardware)
    

#---------------------------------------------------------------------------------
# STUDENT CODE BEGINS
#---------------------------------------------------------------------------------

import random
import time

dispensed_container = ["Material", 0, "Bin#"]
new_container = ["Material", 0, "Bin#"]
container_count = 0
total_container_weight = 0
bot_start_location = [0, 0, 0]
#speed_proximity = 0.55

def calc_avg(data): #find average of data
    total = sum(data)
    points = len(data)
    avg = total / points
    return avg

def initial_container():#dispense first container
    global dispensed_container
    dispensed_container = table.dispense_container(random.randint(1, 6), True) #Dispense the first container
initial_container()

def move_container():#general function to move container from servo table to q-bot
    global total_container_weight
    global container_count

    pick_up_spot = [0.638, 0, 0.253] #Define all the pick-up and drop-off spots
    drop_spot_1 = [-0.118, -0.515 , 0.669]
    drop_spot_2 = [-0.028,-0.523 , 0.669]
    drop_spot_3 = [0.054, -0.522 , 0.669] 
    inital_drop_spot = [0, 0, 0]

    if container_count == 0:#Assigned a drop off spot based on container count
        initial_drop_spot = drop_spot_1
    elif container_count == 1:
        initial_drop_spot = drop_spot_2
    elif container_count == 2:
        initial_drop_spot = drop_spot_3

    arm.move_arm(0.638, 0, 0.253) #Move the q-arm to the pick up spot
    time.sleep(1)
    arm.control_gripper(35) #hold the container 
    time.sleep(1)
    arm.rotate_elbow(-10) #rotate elbow
    time.sleep(1)
    arm.move_arm(initial_drop_spot[0],initial_drop_spot[1] ,initial_drop_spot[2] ) #Move to the desired drop off cite 
    time.sleep(1)
    arm.rotate_elbow(25) #rotate elbow
    time.sleep(1)
    arm.control_gripper(-15)#Drop off the container
    time.sleep(0.5)
    container_count += 1 #Increase the container count by 1
    total_container_weight += (int)(dispensed_container[1]) #Add the container weight to the total mass on the q-bot
    arm.rotate_shoulder(-25)#rotate elbow to avoid collision with next bottle
    arm.rotate_elbow(-25)#rotate elbow
    time.sleep(1)
    arm.home() #return to home position
    time.sleep(0.5)
    

def load_containers(): #This function loads the bot with upto 3 containers based on condition fulfillment 
    global dispensed_container
    global new_container
    global container_count
    global total_container_weight

    arm.home() #Reset the position of the arm 
    time.sleep(0.5)
    bot.rotate(98) #Rotate bot to allow for easier loading 
    time.sleep(1)

    #Move the first container that was already on the rotater
    if container_count == 0:
        move_container()#calling the general function and applying conditions 

    #While loop that keeps running as long as 3 conditons are met
    load_another_container = True
    while load_another_container:
        new_container = table.dispense_container(random.randint(1, 6), True) #Spawn a new random container
        #Check if the new container would satisfy the three conditions if loaded
        if new_container[2] == dispensed_container[2] and total_container_weight + (int)(new_container[1]) <= 90 and container_count < 3: 
            move_container() #Load the new container on the bot as well since it still satisfies the three conditions 
        else:
            load_another_container = False #Set this boolean to false to break the while loop since the new container cannot be loaded on 
    
    bot.rotate(-98) #Rotate the bot back to its original rotation
    time.sleep(0.5)


def transfer_containers(): #This function makes the bot follow the line until the drop off bin is found. 
    global dispensed_container
    global bot_start_location

    bot_start_location = bot.position() #Update the starting position of the bot before it starts its loop around the track 

    target_colour = [1, 0, 0] #This variable stores the rgb values for the color of the target bin 
    if dispensed_container[2] == "Bin01":#Series of if and elif statements that updates the target color for bin
        target_colour = [1, 0, 0] #red
    if dispensed_container[2] == "Bin02":
        target_colour = [0, 1, 0] #green
    if dispensed_container[2] == "Bin03":
        target_colour = [0, 0, 1] #blue
    if dispensed_container[2] == "Bin04":
        target_colour = [1, 0, 1] #purple

    #Activate the color and ultrasonic sensors 
    bot.activate_color_sensor()
    bot.activate_ultrasonic_sensor()

    #Store the inital color and distance readings of the robot as variables 
    read_colour = bot.read_color_sensor() 
    read_distance = bot.read_ultrasonic_sensor()
    
    while read_colour != target_colour or read_distance > 0.15: #While loop keeps running until there is an object in 15cm range and its color matches target color.
        #Series of if and elif statements that set the bot's wheel speeds accordingly based on the positioning of the yellow line on its sensor.  
        #speeds calculated to have good speed proximity where proximity factor = 0.55
        if bot.line_following_sensors() == [1, 1]:
            bot.set_wheel_speed([0.055, 0.055]) #[0.55*0.1, 0.55*0.1]
        elif bot.line_following_sensors() == [1, 0]:
            bot.set_wheel_speed([0.055, 0.099]) #[0.55*0.1, 0.55*0.18]
        elif bot.line_following_sensors() == [0, 1]:
            bot.set_wheel_speed([0.099, 0.055]) #[0.55*0.18, 0.55*0.1]
        elif bot.line_following_sensors() == [0, 0]:
            bot.set_wheel_speed([-0.055, 0.055]) #[-0.55*0.1, 0.55*0.1]
            print("Line Untracked")
        
        read_colour = bot.read_color_sensor()[0] #Update the color reading to the current reading by the sensor
        read_distance = bot.read_ultrasonic_sensor() #Update the distance reading to the current reading by the sensor

    #Deactivate colour and ultrasonic sensors 
    bot.deactivate_color_sensor()
    bot.deactivate_ultrasonic_sensor()


def dump_containers(): #This function moves the container closer to the bin and drops off the containers. 
    global container_count
    global total_container_weight
    
    bot.forward_distance(0.22) #Move the bot towards the bin near its center.
    bot.stop()
    time.sleep(1)

    #Initiate the drop off mechanism to drop the containers into the bin
    bot.activate_linear_actuator()
    bot.dump()
    bot.deactivate_linear_actuator()

    #Reset the container weight and container count to their default values since the current containers have been dropped off
    total_container_weight = 0
    container_count = 0


def return_home(): #This function makes the bot follow the yellow line until its reaches home position 
    global dispensed_container
    global bot_start_location
    
    current_position = bot.position() #Gets the current position of the bot 

    home_validation = False
    while home_validation == False:
        #Series of if and elif statements that set the bot's wheel speeds accordingly based on the positioning of the yellow line on its sensor. 
        if bot.line_following_sensors() == [1, 1]:
            bot.set_wheel_speed([0.055, 0.055]) #[0.55*0.1, 0.55*0.1]
        elif bot.line_following_sensors() == [1, 0]:
            bot.set_wheel_speed([0.055, 0.099]) #[0.55*0.1, 0.55*0.18]
        elif bot.line_following_sensors() == [0, 1]:
            bot.set_wheel_speed([0.099, 0.055]) #[0.55*0.18, 0.55*0.1]
        elif bot.line_following_sensors() == [0, 0]:
            bot.set_wheel_speed([-0.055, 0.055]) #[-0.55*0.1, 0.55*0.1]
            print("Line Untracked")
            
        current_position = bot.position() #Updates the current position of the bot
        #Check to see if the current positon of the bot is equal to the starting position of the bot
        if abs(current_position[0] - bot_start_location[0]) <= 0.05 and abs(current_position[1] - bot_start_location[1]) <= 0.05 and abs(current_position[2] - bot_start_location[2]) <= 0.05:  
            home_validation = True #Sets the boolean variable to true which breaks the while loop 

    bot.forward_distance(0.05) #Move the bot forward a bit to help adjust its positon
    bot.rotate(5) #Rotate the bot a bit to help adjust its position 
    print("Back to home. Time to rest") #Our Hommie makes it to home :)
    bot.stop()

#intializing finctions 
load_containers()
transfer_containers()
dump_containers()
return_home()
dispensed_container = new_container #Set the current container values to the values of the rejected container from the first run 



#---------------------------------------------------------------------------------
# STUDENT CODE ENDS
#---------------------------------------------------------------------------------
