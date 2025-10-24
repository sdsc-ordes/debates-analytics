import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import jsonlines
import os
import argparse
import json

def fetch_meetings(date_start, date_end, organization="UNHRC", meeting_type="", keywords=""):
    org_code = "60.0051"  # Code for UNHRC, can be expanded for other organizations
    
    # Format dates as DD/MM/YYYY for the 'from' and 'to' parameters
    formatted_date_start = datetime.strptime(date_start, "%Y-%m-%d").strftime("%d/%m/%Y")
    formatted_date_end = datetime.strptime(date_end, "%Y-%m-%d").strftime("%d/%m/%Y")

    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/xml"}
    params = {
        "sr": "true",
        "onlyheld": "false",
        "dateFrom": date_start,
        "dateTo": date_end,
        "mid": "",
        "date_range_preselect": "custom",
        "organization": org_code,
        "privpubl": "public",
        "language": "",
        "keywords": keywords,
        "submit": "submit",
        "reset": "reset",
        "from": formatted_date_start,
        "to": formatted_date_end,
    }

    base_url = "https://conf.unog.ch/digitalrecordings/en/api/v3/meetings"
    full_url = requests.Request('GET', base_url, headers=headers, params=params).prepare().url
    #print(f"Requesting URL: {full_url}")

    response = requests.get(full_url, headers=headers)

    if response.status_code == 200:
        root = ET.fromstring(response.content)
        meetings = []
        for meeting in root.findall(".//Meeting"):
            meeting_data = {
                "MeetingId": meeting.get("MeetingId"),
                "Suffix": meeting.get("Suffix"),
                "DPRowNumber": meeting.find("DPRowNumber").text,
                "MeetingRequestId": meeting.find("MeetingRequestId").text,
                "Title": meeting.find("Title").text,
                "RoomNumber": meeting.find("RoomNumber").text,
                "TimeFrom": meeting.find("TimeFrom").text,
                "TimeTo": meeting.find("TimeTo").text,
                "RecordingStart": meeting.find("RecordingStart").text,
                "UniqueNumber": meeting.find("UniqueNumber").text,
                "ClientName": meeting.find("ClientName").text,
                "ClientCode": meeting.find("ClientCode").text,
                "PrivPubl": meeting.find("PrivPubl").text,
                "Exists": meeting.find("Exists").text,
            }
            meetings.append(meeting_data)

            print(f"Fetched meeting {meeting_data['MeetingId']} {meeting_data['Suffix']}")
        return meetings
    else:
        print(f"Failed to fetch data for range {date_start} to {date_end}: {response.status_code}")
        print(f"Requesting URL: {full_url}")
        print("Response Content:", response.content)
        
        return []

def fetch_session_info(meeting_id, suffix):
    url = f"https://conf.unog.ch/digitalrecordings/get_file/public/60.0051/{meeting_id}{suffix}/info.xml"

    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'DNT': '1',  # Do Not Track
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        session_data = {}
        session_element = root.find(".//session")
        
        if session_element is not None:
            session_data["sessionfile"] = session_element.get("sessionfile")
            
            # Extract recording details
            recording_element = session_element.find(".//recording")
            if recording_element is not None:
                session_data["recording"] = {
                    "recorded": recording_element.get("recorded") == "True",
                    "startdate": recording_element.find("startdate").text,
                    "stopdate": recording_element.find("stopdate").text,
                    "starttime": recording_element.find("starttime").text,
                    "stoptime": recording_element.find("stoptime").text,
                    "recordingtime": recording_element.find("recordingtime").text,
                    "archivefile": recording_element.find("archivefile").text
                }
                
                # Add recording file URL
                session_data["recording_url"] = fetch_recording_files(meeting_id, suffix, session_data["recording"]["archivefile"])
                
                # Extract user fields
                userfield_elements = recording_element.find("userfieldlist").findall("userfield")
                session_data["userfields"] = {
                    userfield.get("name"): userfield.get("value")
                    for userfield in userfield_elements
                }
                
                # Extract track list
                track_elements = recording_element.find("tracklist").findall("track")
                session_data["tracks"] = [
                    {
                        "name": track.get("name"),
                        "mediafiles": [
                            media.text for media in track.find("medialist").findall("media")
                        ]
                    }
                    for track in track_elements
                ]
                
                # Extract markers
                marker_elements = recording_element.find("markerlist").findall("marker")
                session_data["markers"] = [
                    {
                        "type": marker.get("type"),
                        "id": marker.get("id"),
                        "name": marker.get("name"),
                        "info": marker.get("info"),
                        "time": marker.get("time"),
                        "timeoffset": marker.get("timeoffset")
                    }
                    for marker in marker_elements
                ]
                
                # Add transcription availability
                session_data["available_transcriptions"] = fetch_transcription_availability(meeting_id, suffix)
        
        return session_data
    else:
        print(f"Failed to fetch session info for {meeting_id} {suffix}: {response.status_code}")
        print(url)
        return None

def fetch_recording_files(meeting_id, suffix, archivefile):
    """Construct URLs to download available recordings for a session based on the archive file."""
    base_url = f"https://conf.unog.ch/digitalrecordings/get_file/public/60.0051/{meeting_id}{suffix}/"
    recording_url = f"{base_url}{archivefile}"
    return recording_url

def fetch_transcription_availability(meeting_id, suffix):
    """Check availability of transcriptions in multiple languages for a given meeting ID and suffix."""
    languages = ["ARABIC", "CHINESE", "ENGLISH", "FRENCH", "SPANISH", "RUSSIAN"]
    available_transcriptions = {}
    
    base_url = f"https://conf.unog.ch/digitalrecordings/get_file/public/60.0051/{meeting_id}{suffix}/"
    
    # Check availability for each language transcription file
    for language in languages:
        transcription_url = f"{base_url}{language}.ts.json"
        response = requests.head(transcription_url)  # Use HEAD request to check if the file exists
        if response.status_code == 200:
            available_transcriptions[language] = transcription_url
        else:
          available_transcriptions[language] = ""
    
    return available_transcriptions

def download_and_uncompress_recording(recording_url, output_path):
    """Download and uncompress the recording file from the given URL to the output directory."""

    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'DNT': '1',  # Do Not Track
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1'
    }

    # Ensure the output directory exists
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    response = requests.get(recording_url, headers=headers)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
    else:
        print(f"Failed to download recording file from {recording_url}: {response.status_code}")

    # Uncompress the downloaded file
    if output_path.endswith(".zip"):
        import zipfile
        with zipfile.ZipFile(output_path, 'r') as zip_ref:
            zip_ref.extractall(output_path.replace(".zip", ""))
    elif output_path.endswith(".tar.gz"):
        import tarfile
        with tarfile.open(output_path, 'r:gz') as tar_ref:
            tar_ref.extractall(output_path.replace(".tar.gz", ""))
    else:
        print("Unknown file format for uncompression.")

def fetch_and_save_meetings(start_date, end_date, output_file, output_folder, organization="UNHRC", meeting_type="", keywords="", download=False):
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
        with jsonlines.open(output_file, mode='r') as reader:
            try:
                last_entry = list(reader)[-1]
                last_date = datetime.strptime(last_entry["TimeFrom"], "%Y-%m-%d %H:%M")
                start_date = max(start_date, last_date + timedelta(days=1))
            except (IndexError, ValueError, KeyError):
                print("Error reading the last entry in JSONL file; starting from the given start date.")

    current_date = start_date

    while current_date <= end_date:
        week_end = min(current_date + timedelta(days=6), end_date)
        print(f"Fetching meetings from {current_date} to {week_end}")
        date_start_str = current_date.strftime("%Y-%m-%d")
        date_end_str = week_end.strftime("%Y-%m-%d")

        # Fetch weekly meetings
        meetings = fetch_meetings(date_start_str, date_end_str, organization, meeting_type, keywords)
        
        # Fetch and append each meeting with session info
        with jsonlines.open(f"{output_folder}/{output_file}", mode='a') as writer:
            for meeting in meetings:
                session_info = fetch_session_info(meeting["MeetingId"], meeting["Suffix"])
                if session_info:
                    meeting["session_info"] = session_info
                writer.write(meeting)  # Save each meeting with session info immediately
        
        current_date = week_end + timedelta(days=1)

        if download:
            print("Downloading meetings")
            for meeting in meetings:
                if "session_info" in meeting:
                    session_info = meeting["session_info"]
                    if "recording_url" in session_info:
                        folder_name = "HRC_" + session_info["recording"]["startdate"] + 'T' + ''.join(session_info["recording"]["starttime"].split(":")[:2])
                        meeting_output_dir = f"/{output_folder}/{folder_name}"
                        recording_url = session_info["recording_url"]
                        print(f"Downloading recording for {recording_url}")

                        download_and_uncompress_recording(recording_url, meeting_output_dir + "/recording.zip")    

                        # save json inside the meeting folder
                        os.makedirs(meeting_output_dir, exist_ok=True)
                        json_output_path = os.path.join(meeting_output_dir, "metadata.json")
                        with open(json_output_path, "w") as json_file:
                            json.dump(meeting, json_file, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and save UNHRC meetings data to a JSONL file.")
    parser.add_argument("--start_date", type=str, default="01/07/2014", help="Start date in DD/MM/YYYY format.")
    parser.add_argument("--end_date", type=str, required=True, help="End date in DD/MM/YYYY format.")
    parser.add_argument("--output_file", type=str, default="meetings.jsonl", help="Output JSONL file.")
    parser.add_argument("--output_folder", type=str, default=".", help="Output Folder")
    parser.add_argument("--organization", type=str, default="UNHRC", help="Organization code.")
    parser.add_argument("--meeting_type", type=str, default="", help="Type of meeting.")
    parser.add_argument("--keywords", type=str, default="", help="Keywords for filtering.")
    parser.add_argument("--download", action="store_true", help="Flag to indicate if download recordings.")

    args = parser.parse_args()

    fetch_and_save_meetings(
        start_date=args.start_date,
        end_date=args.end_date,
        output_file=args.output_file,
        output_folder=args.output_folder,
        organization=args.organization,
        meeting_type=args.meeting_type,
        keywords=args.keywords,
        download=args.download
    )