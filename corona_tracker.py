import requests
from requests_html import HTML
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import time
from csv import reader

def get_data(geo_type='Country', us_state='', geo_name='World'):
	'''
	Function allows for the collection of daily coronavirus data
	geo_type (str): describes the type of place being searched for (Country, State, County)
	us_state (str): only used if geo_type='County'. the relevant US state for the particular county
	geo_name (str): name of place being searched for
	returns: dictionary of daily data
	'''

	# There are three variables that get affected by the geo_type:
	# 1. url: self-explanatory. the data is stored on different pages
	# 2. css_style: on different pages the table element has a different css id
	# 3. name_col_index: the relevant geo_name is in a different column index

	if geo_type == 'Country':
		url = 'https://www.worldometers.info/coronavirus/'
		css_style = '#main_table_countries_today'
		name_col_index = 1
	elif geo_type == 'State':
		url = 'https://www.worldometers.info/coronavirus/country/us/'
		css_style = '#usa_table_countries_today'
		name_col_index = 0
	elif geo_type == 'County':
		url = f'https://www.worldometers.info/coronavirus/usa/{us_state}/'
		css_style = '#usa_table_countries_today'
		name_col_index = 0
	else:
		return 'Error in geo_type'

	r = requests.get(url=url)
	html_text = r.text
	r_html = HTML(html=html_text)

	# Locates the table element that contains the relevant data
	table_html = r_html.find(css_style)[0]

	# Creates list of table row elements
	rows = table_html.find('tr')

	data = dict()
	for row in rows:
		try:
			# checks if the geo_name variable matches the particular row
			if row.find('td')[name_col_index].text == geo_name:
				# Various column names
				items = ['Total Cases', 'New Cases', 'Total Deaths', 'New Deaths', 'Active Cases']

				for x, item in enumerate(items, start=name_col_index + 1):
					# adds key,value pairs of the columns and their assosciated data
					data.update({item: row.find('td')[x].text})
				return data
		except:
			pass

	return 'Error'


def format_email(locations=[]):
	'''
	Turns a list of locations into an HTML-formatted email
	locations (list): a list of dictionaries that outline the data needed for the get_data function
	'''
	assert len(locations) > 0
	html_opening = """
    <html>
        <head></head>
        <body>
    """
	html_closing = """
        </body>
    </html>
    """
	for loc in locations:
		geo_type = loc['geo_type']
		us_state = loc['us_state']
		geo_name = loc['geo_name']

		# Runs get_data function to return a dictionary of data
		data = get_data(geo_type=geo_type, us_state=us_state, geo_name=geo_name)
		total_cases = data['Total Cases']
		new_cases = data['New Cases']
		total_deaths = data['Total Deaths']
		new_deaths = data['New Deaths']
		active_cases = data['Active Cases']
		html_loc = f"""
        <h3>{geo_name}:</h3>
        <p>Active Cases: {active_cases}<br>
            Total Cases: {total_cases}<br>
            New Cases: {new_cases}<br>
            Total Deaths: {total_deaths}<br>
            New Deaths: {new_deaths}
        </p>
        """
		html_opening += html_loc
	html_opening += html_closing
	return html_opening


def send_mail(html_text, subject='Daily Coronavirus Update', from_email={}, to_email=[]):
	'''
	Sends an email
	param text: (str) body of the email\n
	param subject: (str) subject of email\n
	param from_email: (dict) a dictionary of the 'username' & 'password' of the sender\n
	param to_email: (list (str)) a list with the email address to which the email will be sent\n
	returns None
	'''
	assert isinstance(to_email, list)  # if this statement is false, an error will be initiatied
	assert isinstance(from_email, dict)
	assert len(from_email) == 2
	assert len(to_email) == 1

	username = from_email['username']
	password = from_email['password']
	msg = MIMEMultipart('alternative')
	msg['From'] = username
	msg['To'] = ", ".join(to_email)  # turns list into comma seperated values
	msg['Subject'] = subject

	html_part = MIMEText(html_text, 'html')
	msg.attach(html_part)

	msg_str = msg.as_string()

	# login to my smtp server
	server = smtplib.SMTP(host='smtp.gmail.com', port=587)
	server.ehlo()
	# create secure connection
	server.starttls()
	server.login(username, password)
	server.sendmail(username, to_email, msg_str)

	# quit server
	server.quit()


def daily_blast(csv_file, from_email={}):
	'''
	csv_file (str): name of csv file with recipient data
	from_email (dict): a dictionary of the 'username' & 'password' of the sender
	'''

	# Turns csv_file into list of lists
	with open(csv_file, 'r') as read_obj:
		csv_reader = reader(read_obj)
		list_of_rows = list(csv_reader)
		data = list_of_rows[1:]
		print(data)

	# Each row is an email recipient
	for row in data:
		# checks the number of locations that this recipient needs to be updated about
		items = 0
		to_email = row[0]
		for item in row:
			if item != '':
				items += 1
		no_of_locations = int((items - 1) / 3)

		# creates the list of locations needed for the format_email function
		locations = []
		for i in range(no_of_locations):
			geo_type = row[i * 3 + 1]
			state = row[i * 3 + 2]
			geo_name = row[i * 3 + 3]
			locations.append({
				'geo_type': geo_type,
				'us_state': state,
				'geo_name': geo_name
			})

		html_text = format_email(locations=locations)
		# sends email to specific recipient
		send_mail(html_text=html_text,from_email=from_email, to_email=[to_email])


def main(hour=8, minute=25, from_email={}, csv_file='sample.csv'):
	'''
	Checks the time in a continuous loop, waiting to carry out the daily blast
	hour (int): the hour of the day when you want the email to be sent
	minute (int): the minute of the day when you want the email to be sent
	'''
	assert type(hour) == int
	assert type(minute) == int
	now = datetime.datetime.now()
	year = now.year
	month = now.month
	day = now.day

	# The time that the email will be sent is in between dt & dt2
	dt = datetime.datetime(year, month, day, hour, minute)
	dt2 = datetime.datetime(year, month, day, hour, minute + 1)


	while True:
		# if the current time is the allotted time
		if dt < datetime.datetime.now() < dt2:
			daily_blast(csv_file=csv_file, from_email=from_email)

			# resets to search for the same time the next day
			day += 1
			dt = datetime.datetime(year, month, day, hour, minute)
			dt2 = datetime.datetime(year, month, day, hour, minute + 1)

			# sleeps for almost a day
			time.sleep(80000)
		time.sleep(30)


if __name__ == '__main__':
	from_email = {
		'username': 'username@gmail.com',
		'password': 'password'
	}

	main(hour=8, minute=25, from_email=from_email, csv_file='sample.csv')
