# -*- coding: utf-8 -*-
"""
Created on Fri Nov  8 10:57:03 2019

@author: MASSACHUSETTS
"""

#import stuff
import serial
import numpy as np
import time as t
import datetime as dt

#--------------------------------------------------------------
date = str(dt.date.today())
print

experiment = int(raw_input('what type of experiment are you doing?/n /n '
                           '1. Ramp with no incubation /n 2. Ramp with incubation /n '
                           '3. Heat and cool, no incubation /n 4. Heat and cool with incubation'))



lowT = float(raw_input('low temperature setting?')) #enter the temperature bounds you wish to send and the change between
print
highT =  float(raw_input('high temperature setting?')) #time waits
print
delta =  float(raw_input('change in temp between time points?')) #desired temp ramp increment
print
delay =  int(raw_input('how many seconds between each temp change?')) #sleep function only takes seconds
print
incubate_01 = str(raw_input('do you want to incubate at certain temperatures?'))
print
if incubate_01 == 'yes':
    incubate_02 = ((raw_input('what temperatures do you want to incubate at? (separated by a comma)')))
    print 
    incubate_02 =list(map(int,incubate_02.split(',')))
    
    print 
    delay_02 = int(raw_input('how long do you want to incubate for in seconds?'))
if incubate_01 == 'no':
    pass




print
port = raw_input('which port are you connected to? (ie comX)')
print
read_timeout = int(raw_input('how many seconds to wait for TC-720 to recieve data?'))

if read_timeout == 'None':
    read_timeout= None
else:
    read_timeout = int(read_timeout)
#----------------------------------------------------------------




#dictionary for converting between ascii and hex values
hex_ascii = {'a':	61,
'b':62,
'c':63,
'd':64,
'e':65,
'f':66,
'0':30,
'1':31,
'2':32,
'3':33,
'4':34,
'5':35,
'6':36,
'7':37,
'8':38,
'9':39
}

#defining function to convert desired temp setting to 8 character hex representation
def set_temp_hex(x):
    temp = x*10
    hex_temp = [str(i) for i in hex(temp)]
    hex_temp.remove('x')
    if 'L' in hex_temp:
        hex_temp.remove('L')
    if len(hex_temp)<4:
        hex_temp.insert(0,'0')
    return hex_temp

    
#defining function for calculating the 8 bit checksum
def temp_chksum(y):
    check = int('94',16)
    for i in y:
        if i in hex_ascii:
            value = hex_ascii[i]
            value=str(value)
            value = int(value, 16)
            check+=value
            
    scheck = [str(i) for i in hex(check)]
    scheck.remove('x')
    scheck = scheck[-2:]
    return scheck

#defining function that combines the temperature hexadecimal representation
#with the checksum, the send command to change the temp, start of text
#and end of text 
def send_lines(w):
    stx = ['*']
    cmd = ['1','c']
    etx = ['\r']  
    temp_info = set_temp_hex(w)
    checksum = temp_chksum(temp_info)
    code = stx+cmd+temp_info+checksum+etx
    return code

#the following function was taken from the sample code provided
#it converts the read temperature from hex to dec
def hexc2dec(bufp):
        newval=0
        divvy=4096
        for pn in range (1,5):
                vally=ord(bufp[pn])
                if(vally < 97):
                        subby=48
                else:
                        subby=87
                newval+=((ord(bufp[pn])-subby)*divvy)
                divvy/=16
                if(newval > 32767):
                        newval=newval-65536
        return newval
    


# read control sensor temp1
read=['*','0','1','0','0','0','0','2','1','\r']
buf=[0,0,0,0,0,0,0,0,0,0,0,0,0]
send_temps = list(np.arange(lowT,highT+1, delta)) #temp ranges and increment
print 'send temps=', send_temps
print
print
try:
    if incubate_02:
        print 'incubate temps =', incubate_02
except NameError:
    pass
    
#from top of script

send = [] #empty list to dump code lines
incubate_send = []
for temp in send_temps:
    f = send_lines(temp)
    send.append(f)
#print 'the data sent =', send

try:
    
    if delay_02:
        print 'true'
        for i in range(len(incubate_02)):
            data = incubate_02[i]
            j = send_lines(data)
            incubate_send.append(j)
except NameError:
    print 'false'
    
    
print 'the incubation data sent =', incubate_send
print
print
print
print ' the sent ramp data =', send

#open communication to TC-48-20
#makes sure 'comX' is correct
#timeout is a set time to exit if the connection is not successful
ser=serial.Serial(port, 115200, timeout=read_timeout)
output_enable = ['*','3','0','0','0','0','1','8','4','/r']

for pn in range(0,10):
    ser.write((output_enable[pn])) #write the input data 1 character/byte at a time
            # Some customers have noticed an improved communication from the controller with a small (one to four) millisecond delay between characters
            # this delay is optional, however feel free to attempt it in case of any communication problems

start_time = t.time()    
data_file = open('{}'.format(date)+'tempdata.txt','w')
data_file.write('{:>10} {:>10} {:>6} {:>6}\n'.format('time_elasped', 'sent_temp', 'read_temp', 'current_time'))

for i in range(len(send)): 
    sent_temp = send_temps[i]
    
    
    line = send[i]
    line2 = line
    print 'line =', line
    
        
    if line2 in incubate_send:
        print 'entering delay'
        
        print 'line2 =', line2
        for pn in range(0,10):
            ser.write((line2[pn]))
        for pn in range(0,8):
            buf[pn]=ser.read(1) #read each character of buf as 1 byte at a time
            print(buf[pn])
        t.sleep(delay_02)
         
        for pn in range(0,10):
            ser.write((read[pn]))
            
        for pn in range(0,8):
            buf[pn]=ser.read(1)
            print(buf[pn])
        elapsed_time = t.time()-start_time
        temp1=hexc2dec(buf)
        temp1/=10
        print temp1
        current_time = dt.datetime.now().time()
        print current_time
        data_file.write('{:>10} {:>10} {:>6} {:     %H:%M:%S} \n'.format(elapsed_time, 
                sent_temp, temp1, current_time))
        print 'exiting delay'
    else:
        for pn in range(0,10):
                ser.write((line[pn])) #write the input data 1 character/byte at a time
                # Some customers have noticed an improved communication from the controller with a small (one to four) millisecond delay between characters
                # this delay is optional, however feel free to attempt it in case of any communication problems
        for pn in range(0,8):
                buf[pn]=ser.read(1) #read each character of buf as 1 byte at a time
                print(buf[pn])
        
        t.sleep(delay) #wait for set time before recording temperature       
                
        for pn in range(0,10):
                ser.write((read[pn]))
        
        for pn in range(0,8):
                buf[pn]=ser.read(1)
                print(buf[pn])
        elapsed_time = t.time()-start_time
        temp1=hexc2dec(buf)
        temp1/=10
        print temp1
        current_time = dt.datetime.now().time()
        print current_time
        data_file.write('{:>10} {:>10} {:>6} {:     %H:%M:%S} \n'.format(elapsed_time, 
                        sent_temp, temp1, current_time))

data_file.close()
#set the temp back down to 30
bstc = ['*','1','c','0','1','2','c','f','6','\r']
read=['*','0','1','0','0','0','0','2','1','\r']
buf=[0,0,0,0,0,0,0,0,0,0,0,0,0]
cool_down = send_lines(30)

for pn in range(0,10):
        print 'cool_down =', cool_down[pn]
        ser.write((cool_down[pn]))
        # Some customers have noticed an improved communication from the controller with a small (one to four) millisecond delay between characters
        # this delay is optional, however feel free to attempt it in case of any communication problems
for pn in range(0,8):
        buf[pn]=ser.read(1)
        print 'buf = ',(buf[pn])
for pn in range(0,10):
        print 'bst=', read[pn]
        ser.write((read[pn]))







t.sleep(60)

for pn in range(0,8):
        buf[pn]=ser.read(1)
        print'buf =', (buf[pn])
temp1=hexc2dec(buf)
temp1/=10
print temp1  

try:
    if delay_02:
        print 'incubated temperatures =', incubate_02
        print 'incubate delay =', delay_02
        print
        print
        print
        print
        print lowT, '= lowT'
        print highT,'= highT'
        print delta, '= delta'
        print delay, '= delay' 
        print
        print
        print
        ser.close()
        wait=input("PORT CLOSED")
except NameError:
    print
    print
    print
    print
    print lowT, '= lowT'
    print highT,'= highT'
    print delta, '= delta'
    print delay, '= delay' 
    print
    print
    print
    ser.close()
    wait=input("PORT CLOSED")



#set temps correspond to 25-100 degrees in increments of 5
#* refers to start of text
#'1c' is the command for set temp
#the next 4 characters are the 8 character hexidecimal representation of the desired temp*10
#the next 2 characters are the 2 least signigicant digits of the 8 bit check sum ASCII values of the sent info 
         #ie set temp, so 00fa is 119 and the least sig digits are 19
#\r is the return function



#nested 4 loops for changing the temp and returning the temp at set 
#intervals using time.sleep function





