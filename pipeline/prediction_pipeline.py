from config.paths_config import * 
from utils.helpers import *


def hybrid_recommendation(user_id,user_weights=0.7,content_weights=0.3):
    # Get similar users
    similar_users_ = find_similar_users(5964,USER_WEIGHTS_PATH,USER2USER_ENCODED,
                     USER_ENCODED2USER,n=10)
#                     find_similar_users(5964,USER_WEIGHTS_PATH,USER2USER_ENCODED,
# #                        USER_ENCODED2USER,n=10,return_dist=False,neg=False)
    # print("Similar User:",similar_users_)
    
    # Get user preferences
    user_preferences = get_user_preferences(user_id,RATING_DF,DF)
    # print("User_preferences:",user_preferences)
    
    # Get recommendations based on similar users
    recommendations = get_user_recommendations(similar_users_,user_preferences,DF,SYNOPSIS_DF_PATH,RATING_DF,n=10)
    # print(recommendations)
    
    user_recommended_animes_list = recommendations['anime_name'].tolist()
    # print("User based recommended animes:",user_recommended_animes_list)
    
    # Get content-based recommendations
    content_recommended_animes = []
    for anime in user_recommended_animes_list:
        similar_animes = find_similar_animes(anime,ANIME_WEIGHTS_PATH,ANIME2ANIME_ENCODED,
                                            ANIME_ENCODED2ANIME,DF,n=5,return_dist=False,neg=False)
        if similar_animes is not None and not similar_animes.empty:
            content_recommended_animes.extend(similar_animes['anime_name'].tolist())
        else:
            print(f"No similar animes found for {anime}")
        
    
    combine_scores = {}
    for anime in user_recommended_animes_list:
        combine_scores[anime] = combine_scores.get(anime, 0) + user_weights
    for anime in content_recommended_animes:
        combine_scores[anime] = combine_scores.get(anime, 0) + content_weights
    
    sorted_animes = sorted(combine_scores.items(), key=lambda x: x[1], reverse=True)
    
    return [anime for anime,score in sorted_animes[:10]]
