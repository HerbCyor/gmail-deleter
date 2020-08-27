from __future__ import print_function
import pickle
import os.path
from datetime import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

""" Script for deleting e-mails in batches in gmail

    get started at https://developers.google.com/gmail/api/quickstart/python"""

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://mail.google.com/']

def main():

    """Check credentials to start connection os create them if needed"""
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
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    return service

def getAllEmails(*args):
    """ takes gmail search queries as arguments >> return a list of e-mail ids
        if no args are passed, return all e-mails"""
    service = main()
    messages = service.users().messages()
    q = ""
    if args:
        for arg in args:
            q = q + arg + " "
    else:
        q = None
    list_request = messages.list(userId='me',q=q)
    final_email_list = []
    
    email_list = list_request.execute()
    
    def getAllLists(list_request,email_list):
        next_request = messages.list_next(list_request,email_list)
        try:
            next_email_list = next_request.execute()
            for email in next_email_list['messages']:
                final_email_list.append(email['id'])
            return getAllLists(next_request,next_email_list)
        except :
            return False
    
    for email in email_list['messages']:
        final_email_list.append(email['id'])
    
    getAllLists(list_request,email_list)

    return list(dict.fromkeys(final_email_list))
        
def batchDeleteEmails(email_list):
    """deletes messages from gmail in batches of 1000 (limit of the request)"""
    service = main()
    number = len(email_list)
    #checks if the number of entries is > 1000. if so: slice the first 1000, delete and pass the rest of the list through the function
    if number > 1000:                      
        to_delete = {'ids':email_list[:1000]}
        delete_request = service.users().messages().batchDelete(userId='me',body=to_delete)
        delete_request.execute()
        try:
            return batchDeleteEmails(email_list[1000:])
        except IndexError:
            return batchDeleteEmails((email_list))
    else:
        to_delete = {'ids':email_list}
        delete_request = service.users().messages().batchDelete(userId='me',body=to_delete)
        delete_request.execute()

def batchGetandDelete():
    
    running = True
    while running:
        print("Choose emails to delete using query commands as: from:value, to:value, in:value , is:value , separated by commas")
        print("type 'done' or use CTRL+C to quit\n")
        source = input("delete emails: ")
        if source == "done":
            running = False
        else:
            query = source.split(',')
            emails = getAllEmails(*query)
            confirming = True
            while confirming:
                confirmation = input(f"Delete {len(emails)} query = {query[0]}? Y/N:")
                if confirmation == 'Y' or confirmation == 'y':
                    start = datetime.now()
                    batchDeleteEmails(emails)
                    print(f"Deleted {len(emails)} e-mails in {datetime.now()-start} seconds\n")
                    confirming = False
                elif confirmation == 'N' or confirmation == 'n':
                    print("canceled\n")
                    confirming = False
                else:
                    print("not a valid command\n")
    return False
    
if __name__ == '__main__':
    batchGetandDelete()