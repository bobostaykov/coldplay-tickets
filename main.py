import logging as log
import os
import smtplib
import ssl
from email.message import EmailMessage

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

LOG_FILE = 'log.log'
NOTIFIED_CITIES_FILE = 'notified_cities.txt'
URL = 'https://www.coldplay.com/tour'
GET_TICKETS = 'GET TICKETS'


def main():
    try:
        config()
        check()
    except Exception as e:
        log.error(e)


def config():
    """ Configures directories and files """

    load_dotenv()
    log.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', filename=LOG_FILE,
                    level=log.INFO)


def check():
    """ Checks for ticket availability in EU-cities and sends a notification if there is """

    try:
        page = requests.get(URL)
    except requests.exceptions.SSLError:
        # try once more
        page = requests.get(URL)
    soup = BeautifulSoup(page.text, 'html.parser')
    eu_concerts = soup.find_all('a', {'data-filter': 'eu'})
    cities = []
    for concert in eu_concerts:
        if GET_TICKETS in concert.text.upper():
            city = concert.find('h3', {'class': 'show-card__location'}).text
            cities.append(city)
    new_cities = get_new_cities(cities)
    if len(new_cities) > 0:
        notify(new_cities)
    else:
        log.info('No new tickets available')


def notify(cities):
    """ Sends an email about ticket availability """

    sender_email = os.environ.get('SENDER_EMAIL')
    receiver_email = os.environ.get('RECEIVER_EMAIL')
    email_password = os.environ.get('EMAIL_PASSWORD')
    text = f'There are available tickets for Coldplay in {", ".join(cities)}!\n\n{URL}'
    message = EmailMessage()
    message.set_content(text)
    message['Subject'] = 'Coldplay Tickets'
    message['From'] = sender_email
    message['To'] = receiver_email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as server:
        server.login(sender_email, email_password)
        server.send_message(message)
        log.info('Sending email notification')


def get_new_cities(cities):
    """ Returns the cities for which a notification was not yet sent
     and stores the current cities with ticket availability"""

    if os.path.exists(NOTIFIED_CITIES_FILE):
        with open(NOTIFIED_CITIES_FILE, "r+") as file:
            notified_cities = file.read().strip().split(',')
            new_cities = [city for city in cities if city not in notified_cities]
            # Replaces the old content with the new one - this is so
            # that a notification will be sent for a city that sold out,
            # but for which then tickets became available again
            file.seek(0)
            file.write(','.join(cities))
            file.truncate()
            return new_cities
    else:
        with open(NOTIFIED_CITIES_FILE, "w") as file:
            file.write(','.join(cities))
            return cities


if __name__ == '__main__':
    main()
