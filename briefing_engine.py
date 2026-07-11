import datetime
import logging
from dateutil.parser import parse

logger = logging.getLogger("jarvis.briefing")

class BriefingEngine:
    def __init__(self, integrations_manager):
        self.integrations = integrations_manager

    def _get_google_events(self, time_min, time_max, silent=False):
        service = self.integrations.get_google_service('calendar', 'v3', silent=silent)
        if not service:
            return None
            
        try:
            events_result = service.events().list(
                calendarId='primary', 
                timeMin=time_min,
                timeMax=time_max, 
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return events_result.get('items', [])
        except Exception as e:
            logger.error("Failed to fetch Google calendar events: %s", e)
            return []

    def get_todays_agenda(self, silent=False):
        """Fetch today's events for the Smart Sticky-Note."""
        now = datetime.datetime.utcnow()
        time_min = now.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        time_max = now.replace(hour=23, minute=59, second=59).isoformat() + 'Z'
        
        events = self._get_google_events(time_min, time_max, silent=silent)
        if events is None:
            return None
            
        agenda = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'Busy')
            agenda.append({"start": start, "summary": summary})
            
        return agenda

    def get_weekly_agenda(self, silent=False):
        """Fetch the next 7 days of events for the Smart Sticky-Note."""
        now = datetime.datetime.utcnow()
        time_min = now.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        time_max = (now + datetime.timedelta(days=7)).replace(hour=23, minute=59, second=59).isoformat() + 'Z'
        
        events = self._get_google_events(time_min, time_max, silent=silent)
        if events is None:
            return None
            
        agenda = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'Busy')
            agenda.append({"start": start, "summary": summary})
            
        return agenda

    def get_travel_and_appointments(self):
        """Fetch a concise overview of appointments and upcoming travel for the next 3 months."""
        now = datetime.datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        time_max = (now + datetime.timedelta(days=90)).isoformat() + 'Z'
        
        events = self._get_google_events(time_min, time_max)
        
        # Filter for "flight", "travel", "hotel", etc.
        travel_events = []
        upcoming_appointments = []
        
        for event in events:
            summary = event.get('summary', '').lower()
            start = event['start'].get('dateTime', event['start'].get('date'))
            
            if any(keyword in summary for keyword in ["flight", "travel", "hotel", "airport"]):
                travel_events.append({"start": start, "summary": event.get('summary')})
            elif len(upcoming_appointments) < 5:  # Just get the next 5 appointments
                upcoming_appointments.append({"start": start, "summary": event.get('summary')})
                
        return {
            "appointments": upcoming_appointments,
            "travel": travel_events
        }

    def get_monthly_review(self):
        """Fetch past month's events to summarize achievements."""
        now = datetime.datetime.utcnow()
        first_day_of_this_month = now.replace(day=1, hour=0, minute=0, second=0)
        
        # If it's Jan 1, go back to Dec 1 of last year
        if first_day_of_this_month.month == 1:
            first_day_of_last_month = first_day_of_this_month.replace(year=first_day_of_this_month.year-1, month=12)
        else:
            first_day_of_last_month = first_day_of_this_month.replace(month=first_day_of_this_month.month-1)
            
        time_min = first_day_of_last_month.isoformat() + 'Z'
        time_max = first_day_of_this_month.isoformat() + 'Z'
        
        events = self._get_google_events(time_min, time_max)
        return events
