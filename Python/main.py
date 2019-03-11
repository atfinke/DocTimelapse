from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient import errors

from datetime import datetime, timedelta, timezone
import tempfile

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]


def main():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
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

    service = build('drive', 'v3', credentials=creds)

    oldest_date = datetime.now(timezone.utc).astimezone() - timedelta(days=7)
    date_string = oldest_date.isoformat()

    timeFilter = "modifiedTime > '" + str(date_string) + "'"
    timeViewedFilter = "viewedByMeTime > '" + str(date_string) + "'"
    trashFilter = "trashed = false"
    mimeTypeFilter = "mimeType = 'application/vnd.google-apps.document'"

    query = "and".join([
        timeFilter,
        timeViewedFilter,
        trashFilter,
        mimeTypeFilter
    ])

    page_token = None

    results = service.files().list(
        pageSize=10,
        orderBy="name",
        corpus="user",
        spaces='drive',
        fields="nextPageToken, files(id, name)",
        q=query,
        pageToken=page_token
    ).execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        print('Files:')
        for index, item in enumerate(items):
            print(u'[{0}] {1}'.format(index, item['name']))

    while True:
        try:
            doc_num = int(input("Please enter the doc #: "))
            if doc_num >= len(items):
                raise ValueError()
        except ValueError:
            print("Invalid doc #.")
            continue
        else:
            break

    file_id = items[doc_num]['id']

    try:
        revisions = service.revisions().list(
            fileId=file_id, fields="exportLinks").execute()
        # print(revisions)
        print()
    except error:
        print('An error occurred: %s' % error)

    print(revisions)
    pdf_files = []
    revisions = revisions.get('revisions', [])
    for revision in revisions:
        revision_id = revision['id']

        revision_data = service.revisions().get(
            fileId=file_id,
            revisionId=revision_id,
            fields="exportLinks"
        ).execute()

        link = revision_data['exportLinks']['text/plain']
        if link:
            pdf_files.append({'id': revision_id, 'link': link})

    dir = tempfile.gettempdir() + "/"

    last_file_size = 0
    print(dir)
    for index, pdf_link in enumerate(pdf_files):
        print(str(index + 1) + " / " + str(len(pdf_files)))
        resp, content = service._http.request(pdf_link['link'])
        if len(content) != last_file_size:
            last_file_size = len(content)
            with open(dir + str(pdf_link['id']) + '.txt', 'wb') as f:
                f.write(content)
        else:
            print("skipping")


if __name__ == '__main__':
    main()
