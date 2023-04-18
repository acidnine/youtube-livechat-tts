# CONFIGURE TEXT TO SPEECH (TTS)
import pyttsx3
# Create a TTS engine instance
engine = pyttsx3.init()
engine.setProperty('rate', 200)   # Set speech rate
engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0')   # Set TTS voice

import os, re, pickle, json, time, random
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
client_secrets_file = "file-name-of-client-secret.json"

def Authorize():
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
    creds = flow.run_local_server(
        host='localhost',
        port=5500,
        authorization_prompt_message="")
    return creds

creds = None

# Load the credentials from the saved file
if os.path.exists('read_chat_youtube_token.pickle'):
    with open('read_chat_youtube_token.pickle', 'rb') as token:
        creds = pickle.load(token)

# If the credentials don't exist or are invalid, ask the user to authenticate
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        creds = Authorize()
        # Save the credentials to a file for later use
        with open('read_chat_youtube_token.pickle', 'wb') as token:
            pickle.dump(creds, token)

# AUTH/BUILD THE CONNECTION
youtube = googleapiclient.discovery.build('youtube', 'v3', credentials=creds)

def getLiveBroadcastInfo():
    """
    ... NOT SURE WHY IT WILL NOT ALLOW mine WITH broadcastStatus HOWEVER WHEN SORTING BY upcoming IT ONLY RETURNS THE USERS USERS LIVESTREAMS
    """
    request = youtube.liveBroadcasts().list(
        part="snippet,contentDetails,status",
        broadcastStatus="upcoming",
        broadcastType="all"
    )
    response = request.execute()
    items = response.get("items",{})
    if len(items) > 0:
        return items[0].get('id', False)
    else:
        return False
    

def getLiveChatId(LIVE_STREAM_ID):
    """
    It takes a live stream ID as input, and returns the live chat ID associated with that live stream

    LIVE_STREAM_ID: The ID of the live stream
    return: The live chat ID of the live stream.
    """
    stream = youtube.videos().list(part="liveStreamingDetails",id=LIVE_STREAM_ID)
    response = stream.execute()
    print("\nLive Stream Details:  ", json.dumps(response, indent=2))
    
    liveChatId = response['items'][0]['liveStreamingDetails']['activeLiveChatId']
    print("\nLive Chat ID: ", liveChatId)
    return liveChatId


# Access user's channel Name:
def getUserName(userId):
    """
    It takes a userId and returns the userName.

    userId: The user's YouTube channel ID
    return: User's Channel Name
    """
    channelDetails = youtube.channels().list(
        part="snippet",
        id=userId,
    )
    response = channelDetails.execute()
    userName = response['items'][0]['snippet']['title']
    return userName


def main():
    # GET USERS LIVESTREAM BROADCAST INFO
    LIVE_STREAM_ID = getLiveBroadcastInfo()
    if not LIVE_STREAM_ID:
        print('Could not find broadcast info...')
        print()
        LIVE_STREAM_ID = input("Enter the live stream ID: ")
        # LIVE_STREAM_ID LIKE "zvJ01iK_8z1"
    
    liveChatId = getLiveChatId(LIVE_STREAM_ID)
    
    messagesList = []  # List of messages
    
    # getLiveChatId() CONSUMES 1 REQUEST for youtube.api.v3.V3DataVideoService.List
    x = 1
    
    engine.say(f"connected to YouTube chat")
    engine.runAndWait()
    
    sleepTimer = 10000
    
    while (True):
        #
        # REMEMBER YOU ONLY GET 10k QUERIES PER DAY (DEFAULT) AND EACH REQUEST IS EQUAL TO 5 OF THOSE SO 5 SECOND GIVES A MAX OF >3 HOURS
        #
        time.sleep(sleepTimer/1000)
        
        notReadMessages = []  # List of messages not yet read by bot
        
        try:
            # REQUEST LIVE MESSAGES
            liveChat = youtube.liveChatMessages().list(liveChatId=liveChatId,part="snippet")
            response = liveChat.execute()
            x += 1
        except Exception as e:
            print('Error!',str(e))
            engine.say(f"YouTube Error! {str(e)}")
            engine.runAndWait()
            time.sleep(10)
            continue
        
        sleepTimer = response.get('pollingIntervalMillis',10000)
        
        allMessages = response.get('items', [])
        
        # Check if there are any new messages and add them messagesList/notReadMessages list:
        if (len(messagesList) == 0) and len(allMessages) > 0:
            for messages in allMessages:
                userId = messages['snippet']['authorChannelId']
                message = messages['snippet']['textMessageDetails']['messageText']
                messagesList.append((userId, message))
        else:
            for messages in allMessages:
                userId = messages['snippet']['authorChannelId']
                message = messages['snippet']['textMessageDetails']['messageText']
                if (userId, message) not in messagesList:
                    notReadMessages.append((userId, message))
                if (userId, message) not in messagesList:
                    messagesList.append((userId, message))
            print("[",str(x),"] [",time.strftime("%Y%m%d-%H%M%S"),"] New Message: ", notReadMessages)
        
        for message_data in notReadMessages:
            userId = message_data[0]
            message = message_data[1]
            username = getUserName(userId)
            print("Username: ", username, ": ", message)
            # CONSIDER REMOVING CHARS FROM MESSAGES
            #tts_msg = re.sub('[\'!()-[]{};:"\\,<>./?@#$%^&*_~]+', '', message)
            tts_msg = message
            engine.say(f"{username} says {tts_msg}")
            engine.runAndWait()


if __name__ == "__main__":
    main()
