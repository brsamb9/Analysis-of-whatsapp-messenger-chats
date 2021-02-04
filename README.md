# Analysis of Whatsapp and Facebook messages
Toy project used for self-use - should still work for others, but realise it isn't robust.<br>

Output .png files:
- Calender heatmap of message frequency via [cal-plot](https://pythonawesome.com/calendar-heatmaps-from-pandas-time-series-data/),
- Message density,
- Sentiment polarity graph,
- wordclouds of person's word frequencies.
and emoji counts in terminal output.
<br>
Personally used these to create own infographic via [canva](https://www.canva.com/create/infographics/) as a present.

## Steps to replicate 

1) Extract data files from respective message services:<br>
- Whatsapp -> Go on desired chatroom, click settings, more, then export chat to your email address for the .txt file,
- Facebook -> detailed explanation in [link](https://www.zapptales.com/en/download-facebook-messenger-chat-history-how-to/) to get .json files.
<br>
2) Run 'python main.py [..]' where the brackets contains the paths to these files you want to analyse.<br>
3) Enter your name when prompted (as to translate 'you' to your actual name - which is needed for the figures) <br>
4) Check current directory for new .png files!<br>