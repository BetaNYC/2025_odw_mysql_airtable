import os
from dotenv import load_dotenv
import mysql.connector
from phpserialize import unserialize
from json import dumps
from pyairtable import Table, Api
from playwright.sync_api import sync_playwright
import re
from sshtunnel import SSHTunnelForwarder

load_dotenv()

ssh_host = os.getenv('SSH_HOST')
ssh_username = os.getenv('SSH_USERNAME')
ssh_password = os.getenv('SSH_PASSWORD')

mysql_host = os.getenv('MYSQL_HOST') # Use localhost because we are forwarding through SSH
mysql_user = os.getenv('MYSQL_USER')
mysql_pw = os.getenv('MYSQL_PASSWORD')
mysqldb = "2025_open_data_nyc_1"

# Setting up SSH tunnel
tunnel = SSHTunnelForwarder(
    (ssh_host, 22), # SSH server endpoint
    ssh_username=ssh_username,
    ssh_password=ssh_password,
    remote_bind_address=(mysql_host, 3306), # Remote MySQL server endpoint
    local_bind_address=('0.0.0.0', 10022) # Local forwarding port (choose any unused port)
)
    
tunnel.start()

print("SSH tunnel established.")

# Now we can connect to MySQL through the tunnel
db = mysql.connector.connect(
    host='127.0.0.1', # Connect to the local end of the tunnel
    user=mysql_user,
    password=mysql_pw,
    database=mysqldb,
    port=tunnel.local_bind_port # Use the dynamically assigned local port
)

print("Connected to MySQL database.")

with open('get_attendees.sql', 'r') as fil:
    query = fil.read()

cursor = db.cursor()
cursor.execute(query)
attendees = cursor.fetchall()

cursor.close()
db.close()
tunnel.close()

def decodeDict(data):
    if isinstance(data, bytes): return data.decode('utf-8')
    if isinstance(data, dict): return dict(map(decodeDict, data.items()))
    if isinstance(data, tuple):  return map(decodeDict, data)
    return data

#create a new list with columns for airtable
db_records = []
for attendee in attendees:
    id, name, email, airtable_id, zoom_link, other_link, event_name, event_time, event_location, event_url, s_demographics, ticket_name, ticket_time  = attendee
    
    link = zoom_link
    if other_link: link = other_link

    try:
        ticket_time_float = ticket_time.timestamp()
    except:
        ticket_time_float = 0

    if event_url:
        event_url = 'https://2025.open-data.nyc/event/' + event_url
    else:
        event_url = None

    row = {
            'Ticket ID': id, 
            'Name': name,
            'Email': email,
            'Event Name': event_name,
            'Event Date/Time String': event_time, #this is a string..
            'Event Location': event_location,
            'Video Link': link,
            'Event Link': event_url,
            'Ticket Type': ticket_name,
            'Ticket Timestamp': ticket_time_float
    }

    #needs to be linked to a submission
    if airtable_id:
        row['Submission ID'] = [airtable_id]

        if s_demographics:
            b_demographics = bytes(s_demographics, 'utf-8')
            demographics = decodeDict(unserialize(b_demographics))
            # todo: needs a function to help match keys to columns
            #{'organization-or-affiliation': 'Y', 'age': '25-34', 'i-live-in': 'USA, not New York', 'my-preferred-pronouns-are_eca75a2364a843fb5d85ed5818ccecae': 'She/Her/Hers', 'i-identify-as_105f7af663691149d9219a9e76b1dd94': 'Caucasian/White', 'do-you-work-for-government-are-you-a-government-contractor-or-do-you-volunteer-for-government': 'No'}
            #{'organization-or-affiliation': 'X', 'age': '25-34', 'i-live-in': 'USA, not New York', 'my-preferred-pronouns-are_e6df7b9f0603459eac9488689b73de7b': 'They/Them/Theirs', 'my-preferred-pronouns-are_b108c3de48870cc27ca6ecc49f4bf4d2': 'He/Him/His', 'i-identify-as_f7c6bfaec77ca9e0c9ca7dd0a1ae59aa': 'Hispanic/Latinx', 'do-you-work-for-government-are-you-a-government-contractor-or-do-you-volunteer-for-government': 'Yes, Contractor'}
            row['Demographics'] = dumps(demographics)
    else:
        if s_demographics:
            b_demographics = bytes(s_demographics, 'utf-8')
            demographics = decodeDict(unserialize(b_demographics))
            # todo: needs a function to help match keys to columns
 
            row['Demographics'] = dumps(demographics)

    db_records.append(row)

api = Api(os.getenv('AIRTABLE_APIKEY'))
base_id = 'applVbrQQpWtHXSiQ'
table_name = 'tblL7lrWkIPlniQmH'

# get existing ids
ids_dict = api.all(base_id, table_name, fields=['Ticket ID']) #needs formatting
ids_lookup = {}
for record in ids_dict:
    id = record['id']
    ticket_id = record['fields']['Ticket ID']
    ids_lookup[id] = ticket_id
ids = list(ids_lookup.keys())

#delete the ones that no longer exist in MySQL and are still in Airtable
table_ticket_ids = set(ids_lookup.values())
mysql_ticket_ids = set([record['Ticket ID'] for record in db_records])
delete_ticket_ids = list(table_ticket_ids - mysql_ticket_ids)
new_ticket_ids = list(mysql_ticket_ids - table_ticket_ids)

print(f'deleting {len(delete_ticket_ids)} records')
delete_table_ids = [k for k, v in ids_lookup.items() if v in delete_ticket_ids]
api.batch_delete(base_id, table_name, delete_table_ids)

#insert new records into airtable 
new_records = [record for record in db_records if record['Ticket ID'] in new_ticket_ids]
insert_q = api.batch_create(base_id, table_name, new_records)
print(f'adding {len(new_records)} records')

#print total
print(f'Total of {len(db_records)}')

# # get existing views counts
# table_name = 'tbltr6uwQ5FLlTGGY'
# event_views = api.all(base_id, table_name, fields=['View event RSVPs']) 

# events_views_counts = []
# with sync_playwright() as p:
#     browser = p.firefox.launch()
#     page = browser.new_page()
#     for view in event_views:
#         _id = view['id']
#         if 'View event RSVPs' in view['fields']:
#             link = view['fields']['View event RSVPs']
#             page.goto(link)
#             page.wait_for_timeout(1000)
#             try:
#                 records_text = page.text_content('.selectionCount')
#                 numbers = re.findall('[0-9.]+', records_text)
#                 if len(numbers) >= 1:
#                     row = {'id': _id, 'fields': {'# RSVPs': int(numbers[0])}}
#                     events_views_counts.append(row)
#                     print(row)
#                 else:
#                     print('error regex: ', link)
#             except:
#                 print('error link: ', link)

# api.batch_update(base_id, table_name, events_views_counts)
