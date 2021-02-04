import sys
import pandas as pd
import re
from typing import DefaultDict, List

'''
Purpose: infographic about family chats and individuals 
- slight bias as it is only from sender's point of view.
'''

class WhatsappToDF:
    def __init__(self, file: str, sender: str) -> None:
        print("Working on file: {}".format(file))

        f = open(file, "r")
        self.convo = f.read()
        f.close()

        # date and time always preceeds new message: e.g. '15/11/2017, 9:06 am -' -- Very unlikely to have a false positive.
        pattern = "\d{2}\/\d{2}\/\d{4}, \d{1,2}:\d{2} [ap]m -"
        self.date_time_matches = [s.start() for s in re.finditer(pattern, self.convo)]

        self.user = sender
        self.group_creator = ""
        self.group_name = ""
        self.group_members = set()

        # Meta
        self.media_shares = 0
        # other random meta
        self.group_name_changer = DefaultDict(int)
        self.past_group_names = []
        self.icon_changer = DefaultDict(int)
        self.people_adder = DefaultDict(lambda: DefaultDict(int))
        self.people_remover = DefaultDict(lambda: DefaultDict(int))
        self.people_left = DefaultDict(int)
        self.description_changer = DefaultDict(int)


    def into_dataframe(self) -> pd.DataFrame:
        """
        Parsed into dataframe with the following components: date, time, sender, text
        """
        
        messages = self._parse_into_messages()
        data = {'date': [], 'time': [], 'sender': [], 'text': []}

        regex_compile = re.compile(r"(?P<date>\d{2}\/\d{2}\/\d{4}), (?P<time>\d{1,2}:\d{2} [ap]m) - (?P<sender>.*?): ")
        for message in messages:
            parsed_match = regex_compile.match(message)
            if not parsed_match:
                self._custom_whatsapp_lines(message)
            else:
                m = message[parsed_match.end():].strip()
                if "<Media omitted>" == m:
                    self.media_shares += 1
                    continue
                data['date'].append(parsed_match.group('date'))
                data['time'].append(parsed_match.group('time'))
                data['sender'].append(self.name_checker(parsed_match.group('sender')))
                data['text'].append(m)

        self.group_members = list(self.group_members.union(set(data['sender'])))

        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df.date, format='%d/%m/%Y').dt.date
        df['time'] = pd.to_datetime(df['time']).dt.time
        return df

    def meta_info(self) -> dict:
        ''' Return strings of other information '''
        return {
            'group_name': self.group_name,
            'media_shares': self.media_shares,
            'creator': self.group_creator,
            'group_members': self.group_members,
            'past_group_names': self.past_group_names,
            'group_name_changer': self.group_name_changer,
            'icon_changer': self.icon_changer,
            'people_added': self.people_adder,
            'people_removed': self.people_remover,
            'people_left': self.people_left,
            'description_changer': self.description_changer,
        }

    def name_checker(self, name: str) -> str:
        name = "".join(ch for ch in name if ch.isalnum() or ch == ' ')
        name = name.strip()
        return self.user if name.lower() == "you" else name

    def _parse_into_messages(self) -> List[str]:
        """ Helper function - parse conversation into list of messages"""
        # grab ranges - not done too elegantly
        messages = [self.convo[self.date_time_matches[i]:self.date_time_matches[i+1]]
                    for i in range(len(self.date_time_matches) - 1)]
        messages += [self.convo[self.date_time_matches[-1]:]]

        # First message is always the default
        default_message = "Messages and calls are end-to-end encrypted." in messages[0].split('-', 1)[1]
        return messages[1:] if default_message else messages


    def _custom_whatsapp_lines(self, line: str) -> None:
        ''' 
        Helper function - When not a normal message (sent by a person) 
        e.g. 'A' created group, or 'A' added 'B'. 
        Updates class attributes
        '''

        if "created group" in line:
            matchobj_creator = re.findall(
                "(?<=\-).*(?=created group)", line)[0]
            self.group_creator = self.name_checker(matchobj_creator)

            matchobj_group_name = re.findall('\"(.+)\"', line)[0]
            self.group_name = matchobj_group_name.strip()

        elif "added" in line:
            try:
                adder, added = re.findall(
                    "- (.* added .*)", line)[0].split('added')
            except:
                adder = self.user
                added = re.findall("- (.*) was added", line)[0]

            for person_add in [self.name_checker(j) for j in added.split('and')]:
                person_add = person_add.strip()
                self.people_adder[adder.strip()][person_add] += 1
                self.group_members.add(person_add)

        elif "removed" in line:
            kicker, kicked = re.findall(
                "- (.* removed .*)", line)[0].split('removed')
            for removed in [self.name_checker(i) for i in kicked.split('and')]:
                self.people_remover[kicker][removed.strip()] += 1

        elif "changed the subject" in line:
            matchobj_changed_subject = re.findall(
                "- (.*) changed the subject from \".*\" to \"(.*)\"", line)[0]

            changer = self.name_checker(matchobj_changed_subject[0])
            self.group_name_changer[changer] += 1

            new_name = matchobj_changed_subject[1]
            self.past_group_names.append(self.group_name)
            self.group_name = new_name

        elif "left" in line:
            user_left = re.findall("- (.*) left", line)[0].strip()
            self.people_left[self.name_checker(user_left)] += 1

        elif "changed this group's icon" in line:
            member = re.findall(
                "(?<=\-).*(?=changed this group's icon)", line)[0].strip()
            self.icon_changer[self.name_checker(member)] += 1

        elif "changed the group description" in line:
            member = re.findall(
                "(?<=\-).*(?=changed the group description)", line)[0].strip()
            self.description_changer[self.name_checker(member)] += 1

        else:
            sys.exit(
                "Error: It couldn't parse the following: \n\t{}".format(line))