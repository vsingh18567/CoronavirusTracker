import requests
from requests_html import HTML
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import time


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


def send_mail(html_text, subject='Daily Coronavirus Update', from_email={}, to_emails=[]):
	'''
	param text: (str) body of the email\n
	param subject: (str) subject of email\n
	param from_email: (dict) a dictionary of the 'username' & 'password' of the sender\n
	param to_emails: (list (str)) a list of email addresses to which the email will be sent\n
	returns None
	'''
	assert isinstance(to_emails, list)  # if this statement is false, an error will be initiatied
	assert isinstance(from_email, dict)
	assert len(from_email) == 2
	assert len(to_emails) > 0

	username = from_email['username']
	password = from_email['password']
	msg = MIMEMultipart('alternative')
	msg['From'] = username
	msg['To'] = ", ".join(to_emails)  # turns list into comma seperated values
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
	server.sendmail(username, to_emails, msg_str)

	# quit server
	server.quit()


def main(hour=8, minute=25):
	'''
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

	# Turns a list of locations into html_text
	html_text = format_email([
		{'geo_type': 'Country', 'us_state': '', 'geo_name': 'World'},
		{'geo_type': 'Country', 'us_state': '', 'geo_name': 'USA'},
		{'geo_type': 'Country', 'us_state': '', 'geo_name': 'Hong Kong'},
		{'geo_type': 'State', 'us_state': '', 'geo_name': 'Pennsylvania'},
		{'geo_type': 'County', 'us_state': 'Pennsylvania', 'geo_name': 'Philadelphia'}
	])
	from_email = {
		'username': 'email@gmail.com',
		'password': 'password'
	}
	to_emails = ['email1@gmail.com', 'email2@gmail.com']

	while True:
		if dt < datetime.datetime.now() < dt2:
			send_mail(html_text=html_text, from_email=from_email, to_emails=to_emails)
			day += 1
			dt = datetime.datetime(year, month, day, hour, minute)
			dt2 = datetime.datetime(year, month, day, hour, minute + 1)
			time.sleep(80000)  # sleeps for almost a day
		time.sleep(30)


if __name__ == '__main__':
	main()
