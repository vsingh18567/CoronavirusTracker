# Coronavirus Tracker
<code>corona_tracker.py</code> scrapes data from Worldometer's Coronavirus page every day, and sends targeted recipients an email with the daily update on the number of cases/deaths in specific locations (countries, US states, US counties).

## How to use the project
A csv is created with the list of recipients, and the specific locations that they need to be updated about. <code>sample.csv</code> can be accessed to see a sample set-up of the data. Each recipient has their own row, with a maximum of 8 locations for each recipient.

For each location, you need a <code>geo_type</code> (the type of location being searched for - 'Country', 'State', 'County'), <code>us_state</code> (only needed if <code>geo_type='State'</code>) & <code>geo_name</code> (the location being searched for). The default for <code>us_state</code> is NaN if it's not needed. 

Once the CSV has been filled in, the python file can be run. THe <code>main()</code> function is initiated when the python file is run. <code>hour</code> & <code>minute</code> is the time at which you want the email to be sent. This is by default 8:25, as I am located in the +8:30 GMT timezone. The data resets at 00:00 GMT every night, and the email is therefore sent 5 minutes before the data is reset. Change it based on where you are located. The <code>from_email</code> variable is a dictionary with username and password of the E-mail account (needs to be an insecure Gmail id). 

Once it's been initated, the python file can run continuously, sending the daily updates. 
