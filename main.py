import sys
from whatsapp_parser import WhatsappToDF
from facebook_json_parser import FacebookToDF
from dfAnalyzer import * 


def main():
    print("\Creating main DataFrame:\n")
    fresh_df = combine_dataframes(files=sys.argv[1:])
    
    
    print("\nStarting analyzing chat:\n")
    print("\n-- Emoji's analysis:")
    emojisCountsList = list(emoji_counts(fresh_df))
    for name, emojiCounts in emojisCountsList:
        print(name, "\n\t", 'Total emojis: {}'.format(sum(emojiCounts.values())), 
            '\nTop 10 common: {}'.format(emojiCounts.most_common(10)))
        

    print("\n-- Cleaning Data:")
    cleanText_df = clean_up_text(fresh_df)

    print("\n-- Meta-analysis:")
    global_metadata = global_meta(cleanText_df)
    print(global_metadata)
    

    print("\n-- WordCloud Section:")
    masks = True
    # ##### This section needs personalisation
    # # https://regenerativetoday.com/generate-word-clouds-of-any-shape-in-python/
    if masks:
        templateImage = np.array((Image.open("owl_mask.png")))
    else:
        templateImage = None
   
    wordCounts = word_counts(cleanText_df)
    save_wordcloud(cleanText_df, people_said=wordCounts, templateImage=templateImage)


    print("\n-- Message Frequency Section:")
    save_message_frequency(cleanText_df)

    print("\n-- Sentiment analysis Section:")
    save_sentiment_analysis(fresh_df)

    print("\n-- Heatmap calender Section:")
    save_heatmap_calender(fresh_df)



def combine_dataframes(files: List[str]) -> pd.DataFrame:
    extClass = {'txt': WhatsappToDF, 'json': FacebookToDF}

    combine_df = pd.DataFrame(columns=['date', 'time', 'sender', 'text'])
    for file in files:
        fileExt = file.split('.')[-1]
        try:
            convertClass = extClass[fileExt]
        except:
            sys.exit("error: file provided has an unknown file extension type")

        convert = convertClass(file)
        dftoAppend = convert.into_dataframe()
        combine_df = pd.concat([combine_df, dftoAppend], ignore_index=True)

        for (k, v) in convert.meta_info().items():
            print(k, "\t\t", v)

    combine_df = combine_df.sort_values(['date', 'time'], ascending=[True, True])
    return combine_df


if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.exit("Please type in the file path to the whatsapp text file, and/or facebook json file")
    
    main()