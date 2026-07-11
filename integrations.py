import os
import json
import logging
import threading
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import msal

logger = logging.getLogger("jarvis.integrations")

# Google Scopes
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/contacts.readonly',
    'https://www.googleapis.com/auth/userinfo.profile'
]

# Microsoft Settings
AUTHORITY = "https://login.microsoftonline.com/common"
MS_SCOPES = ["Calendars.Read", "Mail.ReadWrite"]

class IntegrationsManager:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.google_creds_file = os.path.join(root_dir, 'google_client_secrets.json')
        self.google_token_file = os.path.join(root_dir, 'google_token.json')
        self.azure_client_id_file = os.path.join(root_dir, 'azure_client_id.txt')
        self.msal_cache_file = os.path.join(root_dir, 'msal_token_cache.bin')
        
        self.google_creds = None
        self.msal_app = None
        
        # Load Azure Client ID
        self.azure_client_id = None
        if os.path.exists(self.azure_client_id_file):
            with open(self.azure_client_id_file, 'r') as f:
                self.azure_client_id = f.read().strip()
        self.auth_url_callback = None

    def get_google_service(self, api_name, api_version, silent=False):
        """Get an authenticated Google API service."""
        if not os.path.exists(self.google_creds_file):
            logger.error("Google client secrets file not found.")
            return None
            
        if self.google_creds and self.google_creds.valid:
            return build(api_name, api_version, credentials=self.google_creds, cache_discovery=False)
            
        if os.path.exists(self.google_token_file):
            try:
                self.google_creds = Credentials.from_authorized_user_file(self.google_token_file, SCOPES)
            except Exception as e:
                logger.warning("Corrupted Google token file found, deleting: %s", e)
                try:
                    os.remove(self.google_token_file)
                except OSError:
                    pass
                self.google_creds = None
            
        if not self.google_creds or not self.google_creds.valid:
            if self.google_creds and self.google_creds.expired and self.google_creds.refresh_token:
                try:
                    self.google_creds.refresh(Request())
                except Exception as e:
                    logger.warning("Google refresh failed, requiring re-auth: %s", e)
                    if silent:
                        return None
                    self._do_google_auth()
            else:
                if silent:
                    return None
                self._do_google_auth()
                
            if self.google_creds:
                with open(self.google_token_file, 'w') as token:
                    token.write(self.google_creds.to_json())
            else:
                return None
                
        return build(api_name, api_version, credentials=self.google_creds, cache_discovery=False)

    def _do_google_auth(self):
        logger.info("Starting Google OAuth flow...")
        flow = InstalledAppFlow.from_client_secrets_file(self.google_creds_file, SCOPES)
        import webbrowser
        original_open = webbrowser.open
        
        def custom_open(url, *args, **kwargs):
            if self.auth_url_callback:
                self.auth_url_callback(url)
            else:
                original_open(url, *args, **kwargs)
                
        webbrowser.open = custom_open
        try:
            self.google_creds = flow.run_local_server(port=0, timeout_seconds=120)
            try:
                oauth2_service = build('oauth2', 'v2', credentials=self.google_creds, cache_discovery=False)
                user_info = oauth2_service.userinfo().get().execute()
                profile_file = os.path.join(self.root_dir, 'google_profile.json')
                with open(profile_file, 'w') as f:
                    json.dump(user_info, f)
            except Exception as e:
                logger.error("Failed to fetch Google user profile: %s", e)
        except Exception as e:
            logger.error("Google authentication failed or timed out: %s", e)
            self.google_creds = None
        finally:
            webbrowser.open = original_open
            
    def get_google_profile(self):
        profile_file = os.path.join(self.root_dir, 'google_profile.json')
        if os.path.exists(profile_file):
            try:
                with open(profile_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def unlink_google(self):
        """Removes the stored Google credentials and resets the authentication state."""
        self.google_creds = None
        profile_file = os.path.join(self.root_dir, 'google_profile.json')
        if os.path.exists(profile_file):
            try:
                os.remove(profile_file)
            except:
                pass
                
        if os.path.exists(self.google_token_file):
            try:
                os.remove(self.google_token_file)
                logger.info("Successfully deleted Google token file.")
                return True
            except Exception as e:
                logger.error("Failed to delete Google token file: %s", e)
                return False
        return True
    def get_ms_token(self, silent=False):
        """Get a valid access token for Microsoft Graph API."""
        if not self.azure_client_id:
            logger.error("Azure Client ID not found.")
            return None
            
        cache = msal.SerializableTokenCache()
        if os.path.exists(self.msal_cache_file):
            cache.deserialize(open(self.msal_cache_file, "r").read())
            
        self.msal_app = msal.PublicClientApplication(
            self.azure_client_id, authority=AUTHORITY, token_cache=cache
        )
        
        accounts = self.msal_app.get_accounts()
        result = None
        if accounts:
            result = self.msal_app.acquire_token_silent(MS_SCOPES, account=accounts[0])
            
        if not result:
            if silent:
                return None
            logger.info("Starting Microsoft Device Flow auth...")
            flow = self.msal_app.initiate_device_flow(scopes=MS_SCOPES)
            if "user_code" not in flow:
                logger.error("Failed to create device flow. %s", json.dumps(flow, indent=4))
                return None
                
            print(f"\n========================================================")
            print(f"MICROSOFT LOGIN REQUIRED: {flow['message']}")
            print(f"========================================================\n")
            
            result = self.msal_app.acquire_token_by_device_flow(flow)
            
        if result and "access_token" in result:
            with open(self.msal_cache_file, "w") as f:
                f.write(cache.serialize())
            return result["access_token"]
        else:
            if result:
                logger.error("Failed to acquire MS token: %s", result.get("error_description", "Unknown error"))
            return None
