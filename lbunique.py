# this is the driver that calculates a metric that defines uniqueness, as follows:
# 'uniqueness' is defined in terms of 'available deviance'.
# 'available deviance' (AD) is the how much the rating could possibly differ from the average,
# defined as max(avg_rating-0.5, avg_rating-5).
# 'uniqueness' is the mean ratio of abs(user_rating-avg) to AD.


import sys
import numpy as np
import pandas as pd
import requests
from selectolax.parser import HTMLParser
import threading
import letterboxdfinders as lbf
import math

LB_HOME = "https://letterboxd.com/"
OUTPUT_WIDTH = 50
NUM_THREADS = 10
LOCK = threading.Lock()


def print_loading_bar(rows_now, total_rows):
    bar_width_now = math.ceil(OUTPUT_WIDTH * (rows_now+1)/total_rows)
    print("| ", "█" * bar_width_now, 
            (OUTPUT_WIDTH - bar_width_now) * " ", "|", 
            f"{(rows_now+1)/total_rows:.0%}",
            end = "\r")



# gets the URLs to the films, as well as user ratings while the page was requested
def get_user_ratings(username):
    print("\nGetting user ratings...")
    user_diary_url = LB_HOME + username + "/films/diary/"
    diary_webpage = requests.get(user_diary_url)
    diary_html = HTMLParser(diary_webpage.text)

    # get last page
    pagination_elements = diary_html.css("li.paginate-page")
    last_page_num = int(pagination_elements[-1].text())


    # get relevant nodes for URLs and user ratings
    url_paths_list = []  # href's only have endings of urls to films
    user_ratings_list = []
    for page_num in range(last_page_num):
        print_loading_bar(page_num, last_page_num)
        current_page = requests.get(user_diary_url + "page/" + str(page_num+1) + "/")
        curr_page_html = HTMLParser(current_page.text)
        url_paths_list += curr_page_html.css("div.film-poster")
        user_ratings_list += curr_page_html.css("span.rating")


    # unpack film keys ("slugs") from div nodes, and complete the URL
    for i, divNode in enumerate(url_paths_list):
        # the 'data-film-slug' attribute is the unique key for the film
        url_paths_list[i] = LB_HOME + "film/" + divNode.attributes["data-film-slug"] + "/"

    
    # user ratings are rendered as strings of star characters,
    # need to parse the list to convert to numbers
    star_string = ""
    full_stars = 0
    half_star = 0
    for i, rating in enumerate(user_ratings_list):
        star_string = rating.text()
        full_stars = star_string.count('★')
        half_star  = star_string.count('½') * 0.5
        user_ratings_list[i] = full_stars + half_star


    urls_user_ratings_dict = {
        'Film URL': url_paths_list,
        'User Rating': user_ratings_list
    }
    user_ratings_df = pd.DataFrame(urls_user_ratings_dict)

    return user_ratings_df


# the function call for threading
def thread_worker():
    global CURRENT_ROW 
    while(CURRENT_ROW < TOTAL_DISTINCT_FILMS):
        LOCK.acquire()
        thread_row = CURRENT_ROW
        CURRENT_ROW += 1           # kicks the row ahead so the current
        LOCK.release()             # thread is never working on the same row

        AVG_RATINGS_DF.iloc[thread_row, 1] = lbf.get_avg_rating(
            AVG_RATINGS_DF.iloc[thread_row, 0])
        print_loading_bar(CURRENT_ROW, TOTAL_DISTINCT_FILMS)



# this gets the site-wide average film rating
def get_avg_rating_col(url_col):
    print("\n\nGetting average ratings...")

    # declaring these as global to access in threads
    global TOTAL_DISTINCT_FILMS
    global AVG_RATINGS_DF
    global CURRENT_ROW

    url_col = list(set(url_col))  # only get average rating once
    TOTAL_DISTINCT_FILMS = len(url_col)

    avg_ratings_dict = {
        "Film URL": url_col,
        "Average Rating": np.zeros((TOTAL_DISTINCT_FILMS), dtype=float)
    }

    # empty dataframe to load ratings into
    AVG_RATINGS_DF = pd.DataFrame(avg_ratings_dict)

    ### simple multithreading implementation
    # what's wild is that it was waayyyy less work to do multithreading
    # than to use something other than Python's super-slow request library.
    # I tried both faster_than_requests and PycURL, and I couldn't get either
    # of them to stop giving me errors. So I multithreaded the part where it 
    # dragged the longest. And I can still have a loading bar!
    all_threads = []
    CURRENT_ROW = 0
    for i in range(NUM_THREADS):
        all_threads.append(threading.Thread(target=thread_worker, daemon=True))

    for i in range(NUM_THREADS):
        all_threads[i].start()

    for i in range(NUM_THREADS):
        all_threads[i].join()
    
    
    print()  # to put carriage on new line after loading bar function

    return AVG_RATINGS_DF



# is the average closer to the low end or the high end?
def get_available_dev(average_rating):
    return max(average_rating-0.5, 5-average_rating)


# 'uniqueness' is defined in terms of 'available deviance'.
# 'available deviance' (AD) is the how much the rating could possibly differ from the average,
# defined as max(avg_rating-0.5, avg_rating-5).
# 'uniqueness' is the mean ratio of abs(user_rating-avg) to AD.
def calc_uniqueness(ratings_only):
    print("\nCalculating uniqueness...")

    ratings_only['Absolute Difference'] = abs(ratings_only['Average Rating'] - ratings_only['User Rating'])
    ratings_only['Available Deviance']  = ratings_only['Average Rating'].apply(get_available_dev)
    ratings_only['Uniqueness'] = ratings_only['Absolute Difference'] / ratings_only['Available Deviance']

    return ratings_only['Uniqueness'].mean()


def is_valid_user(username):
    print("\nValidating username...")
    
    userpage = requests.get(LB_HOME+username)
    userpage_html = HTMLParser(userpage.text)
    error_elements = userpage_html.css("body.error")

    return not bool(len(error_elements))


def main():

    user = sys.argv[1]  # first CL arg is the program name, the next is the username
    if (is_valid_user(user)):
        ratings_df = get_user_ratings(user)  # starts with the URLs and user ratings
        
        # since list of avg ratings is only distinct films, it might be shorter, 
        # so it needs SQL-like join to bring it into the dataframe
        ratings_df = ratings_df.merge(
            get_avg_rating_col(ratings_df['Film URL']), 
            on='Film URL')  

        uniqueness = calc_uniqueness(ratings_df[['User Rating', 'Average Rating']])
        print(f"\nUniqueness score for {user}: {round(uniqueness,4)}\n")
    else:
        print("\nInvalid username. Try again with a different username.\n")




if (__name__ == "__main__"):
    main()