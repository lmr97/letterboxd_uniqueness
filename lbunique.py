# this is the driver that calculates a metric that defines uniqueness, as follows:
# 'uniqueness' is defined in terms of 'available deviance'.
# 'available deviance' (AD) is the how much the rating could possibly differ from the average,
# defined as max(avg_rating-0.5, avg_rating-5).
# 'uniqueness' is the mean ratio of abs(user_rating-avg) to AD.


import sys
import numpy as np
import pandas as pd
#import pycurl
import requests
from selectolax.parser import HTMLParser
import concurrent.futures
import letterboxdfinders as lbf
import math
import time

LB_HOME = "https://letterboxd.com/"
OUTPUT_WIDTH = 50



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


    # unpack URLs from div nodes, and add homepage
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
    


# this gets the site-wide average film rating
def get_avg_rating_col(url_col):
    print("\n\nGetting average ratings...")

    total_films = url_col.size
    np_col = np.empty((total_films,1), dtype=float)

    # concurrency implementation
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        np_col = executor.map(lbf.get_avg_rating, url_col)
    
    print()  # to put carriage on new line after loading bar function
    avg_ratings_df = pd.DataFrame(np_col, columns=['Average Rating'])
    return avg_ratings_df


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
        ratings_df = ratings_df.join(get_avg_rating_col(ratings_df['Film URL']))  # get average ratings

        uniqueness = calc_uniqueness(ratings_df[['User Rating', 'Average Rating']])
        print(f"\nUniqueness score for {user}: {round(uniqueness,4)}\n")
    else:
        print("\nInvalid username. Try again with a different username.\n")




if (__name__ == "__main__"):
    main()