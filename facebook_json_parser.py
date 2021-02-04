import json
import pandas as pd
import sys

class FacebookToDF():
    def __init__(self, jsonFile: str) -> None:
        try:
            f = open(jsonFile)
        except:
            sys.exit("Error: couldn't read file")

        jsonData = json.load(f)
        f.close()

        self.people = jsonData['participants']
        self.messages = jsonData['messages']
        self.meta = {'Call': 0, 'Share': 0, 'videos': 0, 'photos': 0, 'files': 0}

    def into_dataframe(self) -> pd.DataFrame:
        data = {'datetime': [], 'date': [], 'time': [], 'sender': [], 'text': []}
        for message in self.messages:
            if message['type'] != 'Generic':
                self.meta[message['type']] += 1
            else:
                keys =  message.keys()
                if 'content' in keys:
                    ms_to_datetime = pd.to_datetime(message['timestamp_ms'], unit='ms')
                    data['datetime'].append(ms_to_datetime)
                    data['date'].append(ms_to_datetime.date())
                    data['time'].append(ms_to_datetime.time())
                    data['sender'].append(self.name_checker(message['sender_name']))
                    data['text'].append(message["content"])
                else:
                    for key in keys:
                        try:
                            self.meta[key] += 1
                        except:
                            pass
                            
        df = pd.DataFrame(data)
        df = df.sort_values('datetime').reindex(range(df.shape[0]))
        return df.drop('datetime', axis=1)

    def meta_info(self) -> dict:
        return self.meta

    def name_checker(self, name: str) -> str:
        name = "".join(ch for ch in name if ch.isalnum() or ch == ' ')
        name = name.strip()
        
        return self.user if name.lower() == "you" else name
