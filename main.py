import os
from dotenv import load_dotenv
import mysql.connector
from phpserialize import unserialize
from json import dumps
from pyairtable import Table, Api

load_dotenv()

#read from the database
db = mysql.connector.connect(
    host= os.getenv('MYSQL_HOST'),
    user= os.getenv('MYSQL_USER'),
    password= os.getenv('MYSQL_PASSWORD'),
    database="2023_open_data_nyc"
)

with open('get_attendees.sql', 'r') as fil:
    query = fil.read()

cursor = db.cursor()
cursor.execute(query)
attendees = cursor.fetchall()


def decodeDict(data):
    if isinstance(data, bytes): return data.decode('utf-8')
    if isinstance(data, dict): return dict(map(decodeDict, data.items()))
    if isinstance(data, tuple):  return map(decodeDict, data)
    return data

#create a new list with columns for airtable
db_records = []
for attendee in attendees:
    id, name, email, airtable_id, zoom_link, other_link, event_name, event_url, s_demographics, ticket_name  = attendee
    
    link = zoom_link
    if other_link: link = other_link

    if event_url:
        event_url = 'https://2023.open-data.nyc/event/' + event_url
    else:
        event_url = None

    row = {
            'Ticket ID': id, 
            'Name': name,
            'Email': email,
            'Event Name': event_name,
            'Video Link': link,
            'Event Link': event_url,
            'Ticket Type': ticket_name
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
base_id = 'appBTbKiW8ZuPRcaF'
table_name = 'READ ONLY: ODW Attendees'

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
