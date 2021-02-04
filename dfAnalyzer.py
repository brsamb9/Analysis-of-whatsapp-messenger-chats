# from datetime import datetime
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

import re
from os import path 
from PIL import Image

import calplot

#https://github.com/jcalcutt/projects/blob/master/nlp_whatsapp/nlp_whatsapp.ipynb
# import nltk
# nltk.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer 

from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import emoji

from collections import Counter
from typing import Dict, Generator, List
from functools import reduce


def clean_up_text(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Removes all emojis, punctuation, stopwords, etc within messages.
    '''
    df = df.copy()
    stopWords = set(STOPWORDS)
    def _clean_up(s: str) -> str:
        s = s.lower()
        charsCheck = "".join([c for c in s if c.isalpha() or c == ' '])
        return " ".join([word for word in charsCheck.split() if word not in stopWords])
    df['text'] = df['text'].apply(_clean_up)
    return df

def global_meta(df: pd.DataFrame) -> Dict:
    '''
    Some random metadata about the messages as overall
    - Total messages sent (all parties)
    - How long since the first message to the latest
    - Average per day
    - Day counts
    - Senders counts
    '''
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_series = df['date'].apply(lambda x: days[x.weekday()])
    mostCommonDays = day_series.value_counts().to_dict()

    # welcome to time hell - https://stackoverflow.com/questions/13703720/converting-between-datetime-timestamp-and-datetime64#21916253
    startDay, endDay = df['date'].min(), df['date'].max()
    dateRange = pd.date_range(start=startDay, end=endDay)
    # https://stackoverflow.com/questions/54174811/pandas-timestamp-to-datetime-datetime
    daysMissed = len( pd.DatetimeIndex(dateRange).difference(pd.DatetimeIndex(df['date'])) )
    dayRange = (endDay - startDay).days
    senders = df.sender.unique().tolist()

    return {
        'TotalMessages': df.shape[0],
        'daysMissed': daysMissed,
        'Range': dayRange,
        'AvgPer': {'day': round(df.shape[0] / dayRange, 2), 'year': round(df.shape[0] / (dayRange/365), 2)},
        'DayFreq': mostCommonDays,
        'EachSent': {sender: df[df.sender == sender].shape[0] for sender in senders}
    }

def emoji_counts(df: pd.DataFrame) -> Generator:
    '''Counts the number of emojies used per person -> outputs a lazy generator'''
    _extract_emojis = lambda s : " ".join(c for c in s if c in emoji.UNICODE_EMOJI)
    for person in df['sender'].unique():
        emojis_series = df[df['sender'] == person]['text'].apply(_extract_emojis).values
        emojis = reduce(list.__add__, [emojis_line.split() for emojis_line in emojis_series])
        yield person, Counter(emojis)


def word_counts(df: pd.DataFrame, groupList: List[str]=None) -> Generator:
    '''Counts unique words used per person -> outputs a lazy generator'''
    if groupList is None:
        groupList = df['sender'].unique().tolist()
    for name in groupList:
        c =  " ".join(df[df['sender'] == name]['text'].to_list())
        yield name, Counter(c.split())


def save_message_frequency(df: pd.DataFrame, groupName: str=None):
    '''
    Saves a cool graphic - shamelessly stole and adapted from
        https://github.com/jcalcutt/projects/blob/master/nlp_whatsapp/nlp_whatsapp.ipynb
    '''
    df = df.copy()
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df['day'] = df['date'].apply(lambda x: days[x.weekday()])
    df['datetime'] = pd.to_datetime(df['date'].apply(str) + ' ' + df['time'].apply(str))
    df['float_time'] = df.datetime.dt.hour + df.datetime.dt.minute / 60.0
    df['day_num'] = df.datetime.dt.dayofweek
    df = df.sort_values('day_num')

    days_freq = list(df.day.value_counts().index)
    
    pal = sns.cubehelix_palette(7, rot=-.25, light=.7)
    lst = dict(zip(days, pal[::-1]))
    pal_reorder= [lst[i] for i in days_freq]
    
    sns.set(style="white", rc={"axes.facecolor": (0, 0, 0, 0)})
    pal = sns.cubehelix_palette(7, rot=-.25, light=.7)
    g = sns.FacetGrid(df[(df.float_time > 6)], row="day", hue="day",   
                    aspect=10, height=2.5, palette=pal_reorder, xlim=(6,24))

    # Draw the densities in a few steps
    g.map(sns.kdeplot, "float_time", clip_on=False, shade=True, alpha=1)
    g.map(sns.kdeplot, "float_time", clip_on=False, color="w")
    g.map(plt.axhline, y=0, lw=1, clip_on=False)

    # Define and use a simple function to label the plot in axes coordinates
    def label(x, color, label):
        ax = plt.gca()
        ax.text(0, 0.1, label, fontweight="bold", color=color, 
                ha="left", va="center", transform=ax.transAxes, size=18)

    g.map(label, "float_time")
    g.set_xlabels('Time of Day', fontsize=30)
    g.set_xticklabels(fontsize=20)
    # Set the subplots to overlap
    g.fig.subplots_adjust(hspace=-0.5)
    g.fig.suptitle('Message Density by Time and Day of the Week, Shaded by Total Message Count', fontsize=22)   
    g.set_titles("")
    g.set(yticks=[])
    g.despine(bottom=True, left=True)
    g.tight_layout()
    g.savefig('MessageDensity{}.png'.format(groupName if groupName else "")) 


def save_wordcloud(df: pd.DataFrame, people_said=None, groupName: str=None, templateImage=None) -> None: 
    '''
    Creates a wordcloud .png file - can provide a template assuming not too complex, used default parameters.
    '''
    if people_said is None:
        people_said = word_counts(df)
        
    stopWords = set(STOPWORDS)
    for name, counter in people_said:
        wordcloud = WordCloud(stopwords=stopWords, 
            background_color="white", mask=templateImage, 
            # contour_width=1.5, contour_color="blue",
            width=400, height=1000).generate_from_frequencies(counter)
        plt.figure()
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.tight_layout(pad=0)
        plt.savefig("wordcloud_{}{}.png".format(name, "_" + groupName if groupName else ""))


def save_sentiment_analysis(df: pd.DataFrame) -> None:
    sid = SentimentIntensityAnalyzer()
    df['pol'] = df['text'].apply(lambda x: sid.polarity_scores(x)['compound'])

    df2 = pd.DataFrame(columns=['date', 'sender', 'mean_pol'])
    for k, v in df.groupby(['date','sender'])['pol'].mean().items():
        df2 = df2.append({'date': k[0], 'sender':k[1], 'mean_pol': v}, ignore_index=True)

    sns.set_style("whitegrid")
    plt.figure(figsize=(10, 4))
    sns.scatterplot(x=df2.date, y=df2.mean_pol, hue=df2.sender, alpha=0.2, legend=False)
    #https://stackoverflow.com/questions/13996302/python-rolling-functions-for-groupby-object
    df2['rol'] = df2.groupby('sender')['mean_pol'].rolling(10).mean().reset_index(0,drop=True)
    sns.lineplot(x=df2.date, y=df2.rol, hue=df2.sender)
    plt.title("Sentiment analysis time series")
    plt.ylabel('Polarity')
    plt.tight_layout()
    plt.savefig("sentimentPolarity.png")


def save_heatmap_calender(df: pd.DataFrame) -> None:
    # https://pythonawesome.com/calendar-heatmaps-from-pandas-time-series-data/
    startDay, endDay = df['date'].min(), df['date'].max()
    daysRange = pd.date_range(start=startDay, end=endDay)
    daysDiff = pd.DatetimeIndex(daysRange).difference(pd.DatetimeIndex(df['date']))

    daysMissed = pd.Series({d: 0 for d in daysDiff.values})
    daysCounts = pd.Series(df['date'].apply(pd.to_datetime).value_counts().to_dict())
    allDaysCounts = pd.concat([daysMissed, daysCounts]).sort_index(ascending=True)
    calplot.calplot(allDaysCounts, cmap='plasma', linewidth=2)
    # weirdly offcenter
    plt.subplots_adjust(left=0.05)
    plt.savefig('calender_heatmap.png')