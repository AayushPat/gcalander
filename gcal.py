import os
import logging
import requests
from dateutil import parser
from google.oauth2 import service_account
from googleapiclient.discovery import build

# -------------------------------
# CONFIGURATION
# -------------------------------
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
CANVAS_API_URL = "https://canvas.jmu.edu/api/v1"
CANVAS_API_TOKEN = os.getenv("CANVAS_API_TOKEN", "your_canvas_token_here")
SERVICE_ACCOUNT_FILE = "gold-courage-436803-t1-0e34ed0c5447.json"
TIMEZONE = "America/New_York"

# -------------------------------
# LOGGING SETUP
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# -------------------------------
# GOOGLE CALENDAR AUTHENTICATION
# -------------------------------
def authenticate_google_calendar():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('calendar', 'v3', credentials=creds)

# -------------------------------
# CANVAS API HELPERS
# -------------------------------
def get_canvas_session():
    session = requests.Session()
    session.headers.update({'Authorization': f'Bearer {CANVAS_API_TOKEN}'})
    return session

def fetch_courses(session):
    url = f"{CANVAS_API_URL}/courses"
    response = session.get(url)
    response.raise_for_status()
    return response.json()

def fetch_assignments(session, course_id):
    url = f"{CANVAS_API_URL}/courses/{course_id}/assignments"
    response = session.get(url)
    response.raise_for_status()
    return response.json()

# -------------------------------
# GOOGLE CALENDAR EVENT CREATION
# -------------------------------
def create_calendar_event(service, assignment):
    due_date_str = assignment.get('due_at')
    if not due_date_str:
        logging.warning(f"Skipping '{assignment['name']}': No due date.")
        return

    try:
        due_time = parser.isoparse(due_date_str)
        event = {
            'summary': assignment['name'],
            'start': {'dateTime': due_time.isoformat(), 'timeZone': TIMEZONE},
            'end': {'dateTime': due_time.isoformat(), 'timeZone': TIMEZONE},
        }

        created_event = service.events().insert(calendarId='primary', body=event).execute()
        logging.info(f"Added '{assignment['name']}' to Google Calendar. Event ID: {created_event.get('id')}")

    except Exception as e:
        logging.error(f"Error adding '{assignment['name']}': {e}")

# -------------------------------
# MAIN WORKFLOW
# -------------------------------
def main():
    logging.info("Starting Canvas to Google Calendar sync...")

    session = get_canvas_session()
    calendar_service = authenticate_google_calendar()

    try:
        courses = fetch_courses(session)
        if not courses:
            logging.info("No courses found.")
            return

        all_assignments = []
        for course in courses:
            assignments = fetch_assignments(session, course['id'])
            logging.info(f"Fetched {len(assignments)} assignments for course '{course.get('name', 'Unknown')}'.")
            all_assignments.extend(assignments)

        if not all_assignments:
            logging.info("No assignments to add.")
            return

        for assignment in all_assignments:
            create_calendar_event(calendar_service, assignment)

        logging.info("Sync completed successfully.")

    except requests.HTTPError as e:
        logging.error(f"HTTP Error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

if __name__ == '__main__':
    main()
