from __future__ import print_function
from datetime import datetime as dt
import datetime
import re
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Hangouts bot specially for wikr.com and fabiosamedia

# Rialto prefix is used for separating meeting room calendars
# from other calendaries.
RIALTO_PREFIX = 'БЦ Риальто'
MAX_CALENDAR_RESULTS = 1
DEFAULT_TIMEZONE = 'Europe/Kiev'
EVENTS_ORDER_BY = 'startTime'
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def get_credentials():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds


def init_google_api_service(credentials):
    return build('calendar', 'v3', credentials=credentials)


def get_calendars_from_api(service):
    return service.calendarList().list().execute()['items']


def get_filtered_calendars(calendars):
    return [calendar for calendar in filter(lambda calendar: calendar['summary'].find(RIALTO_PREFIX) != -1, calendars)]


def get_events_from_calendar(calendar, service, min_time):
    response = service.events().list(calendarId=calendar['id'], timeMin=min_time, maxResults=MAX_CALENDAR_RESULTS,
                                     singleEvents=True, timeZone=DEFAULT_TIMEZONE, orderBy=EVENTS_ORDER_BY).execute()
    return response.get('items', [])


def parse_rfc3339(dt):
    broken = re.search(
        r'([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(\.([0-9]+))?(Z|([+-][0-9]{2}):([0-9]{2}))',
        dt)
    return (datetime.datetime(
        year=int(broken.group(1)),
        month=int(broken.group(2)),
        day=int(broken.group(3)),
        hour=int(broken.group(4)),
        minute=int(broken.group(5)),
        ))


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    credentials = get_credentials()
    service = init_google_api_service(credentials)
    calendars = get_calendars_from_api(service)
    filtered_calendars = get_filtered_calendars(calendars)
    min_time = dt.utcnow().isoformat() + 'Z'
    free_rooms = []

    for calendar in filtered_calendars:
        events = get_events_from_calendar(calendar, service, min_time)
        closest_event = events[0]
        start_time = parse_rfc3339(closest_event['start'].get('dateTime'))
        end_time = parse_rfc3339(closest_event['end'].get('dateTime'))
        now = datetime.datetime.now()
        is_room_busy = start_time.isoformat() < now.strftime("%Y-%m-%d %H:%M:%S") < end_time.isoformat()

        if not is_room_busy:
            free_rooms.append('{0}, is free till {1}'.format(calendar['summary'], start_time))

    for room in free_rooms:
        print(room)


if __name__ == '__main__':
    main()
