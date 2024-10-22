import os
import datetime
import requests
from dateutil import parser
from google.oauth2 import service_account
from googleapiclient.discovery import build

# SCOPES define the API permissions
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

CANVAS_API_URL = "https://canvas.jmu.edu/api/v1"
CANVAS_API_TOKEN = "19~vLfZDvtYR3vDQTuLDwthMQUwvKVa9QBGA8D7JBKnYCJz7xxxRerV4ECK6TuLm267"  # Replace with your own Canvas API token

def authenticate_google_calendar():
    """Authenticate and return the Google Calendar service."""
    creds = service_account.Credentials.from_service_account_file(
        'gold-courage-436803-t1-0e34ed0c5447.json', scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    return service

def fetch_courses():
    """Fetch all courses from Canvas."""
    url = f"{CANVAS_API_URL}/courses"
    headers = {'Authorization': f'Bearer {CANVAS_API_TOKEN}'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch courses: {response.status_code} {response.text}")
        return []

def fetch_assignments(course_id):
    """Fetch assignments for a given course ID."""
    url = f"{CANVAS_API_URL}/courses/{course_id}/assignments"
    headers = {'Authorization': f'Bearer {CANVAS_API_TOKEN}'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch assignments for course ID {course_id}: {response.status_code} {response.text}")
        return []

def add_to_google_calendar(assignments):
    """Add assignments to Google Calendar."""
    service = authenticate_google_calendar()

    for assignment in assignments:
        if assignment.get('due_at'):
            try:
                due_time = parser.isoparse(assignment['due_at'])
                event = {
                    'summary': assignment['name'],
                    'start': {
                        'dateTime': due_time.isoformat(),
                        'timeZone': 'America/New_York',  # Adjust as needed
                    },
                    'end': {
                        'dateTime': due_time.isoformat(),
                        'timeZone': 'America/New_York',
                    },
                }
                
                # Insert event into Google Calendar
                service.events().insert(calendarId='primary', body=event).execute()
                print(f"Added assignment '{assignment['name']}' to Google Calendar.")
            except Exception as e:
                print(f"An error occurred while adding '{assignment['name']}': {e}")
        else:
            print(f"No due date for assignment: {assignment['name']}")

def main():
    """Main function to fetch courses and assignments, and add them to Google Calendar."""
    courses = fetch_courses()
    
    all_assignments = []
    
    for course in courses:
        course_id = course['id']
        assignments = fetch_assignments(course_id)
        
        # Print fetched assignments for debugging
        for assignment in assignments:
            print(f"Fetched assignment: {assignment['name']}, Due At: {assignment.get('due_at')}")
        
        all_assignments.extend(assignments)

    if all_assignments:
        add_to_google_calendar(all_assignments)
    else:
        print("No assignments to add to Google Calendar.")

if __name__ == '__main__':
    main()
