import pandas as pd 
import numpy as np 
import joblib 
from config.paths_config import *

################# 1. GET_ANIME_FRAME

def getAnimeFrame(anime,path_df):
  df = pd.read_csv(path_df)
  if isinstance(anime,int):
    return df[df['MAL_ID'] == anime]
  if isinstance(anime,str):
    return df[df['eng_version'] == anime]
  

##################### 2. GET_SYSNOPSIS 
def getSypnopsis(anime,path_synopsis_df):
  synopsis_df = pd.read_csv(path_synopsis_df)
  if isinstance(anime,int):
    return synopsis_df[synopsis_df['MAL_ID'] == anime]['sypnopsis'].values[0]
  if isinstance(anime,str):
    return synopsis_df[synopsis_df['Name'] == anime]['sypnopsis'].values[0]
  

#################### 3.content Recommendation 

def find_similar_animes(name,path_anime_weights,path_anime2anime_encoded,
                        path_encoded2anime,path_df,n=10,return_dist=False,neg=False):

  try:
    anime_weights = joblib.load(path_anime_weights)
    anime2anime_encoded = joblib.load(path_anime2anime_encoded)
    encoded2anime = joblib.load(path_encoded2anime)

  
    index = getAnimeFrame(name,path_df).MAL_ID.values[0]
    encoded_index = anime2anime_encoded.get(index)
    weights = anime_weights


    dists = np.dot(weights,weights[encoded_index])

    sorted_dists = np.argsort(dists)

    n = n+1

    if neg:
      closest = sorted_dists[:n]

    else:
      closest = sorted_dists[-n:]


    print(f" Anime closest to {name}")

    if return_dist:
      return dists,closest

    similarityArr = []

    for close in closest:
      decoded_id = encoded2anime.get(close)

      # synopsis = getSypnopsis(decoded_id,synopsis_df)


      anime_frame = getAnimeFrame(decoded_id,DF)

      anime_name = anime_frame.eng_version.values[0]

      genre = anime_frame.Genres.values[0]

      similarity = dists[close]


      similarityArr.append(
          {
              "anime_id":decoded_id,
              "anime_name":anime_name,
              "genre":genre,
              "similarity":similarity,
          }
      )

    Frame = pd.DataFrame(similarityArr).sort_values(by="similarity",ascending=False)
    return Frame[Frame.anime_id != index].drop(['anime_id'], axis=1)

  except Exception as e :
    print("Error Occurs ",e)


##################################4. user recommendation 

def find_similar_users(item_input,path_user_weights,path_user2user_encoded,
                       path_encoded2user,n=10,return_dist=False,neg=False):
    try:
        
        user_weights = joblib.load(path_user_weights)
        user2user_encoded = joblib.load(path_user2user_encoded)
        encoded2user = joblib.load(path_encoded2user)

        index = item_input
        encoded_index = user2user_encoded.get(index)
        weights = user_weights
        dists = np.dot(weights,weights[encoded_index])
        sorted_dists = np.argsort(dists)
        if neg:
            closest = sorted_dists[:n]
        else:
            closest = sorted_dists[-n:]
        
        if return_dist:
            return dists,closest
        
        similarityArr = []

        for close in closest:
            similarity = dists[close]

            if isinstance(item_input,int):
                decoded_id = encoded2user.get(close)
                similarityArr.append(
                    {
                        "similiar_users":decoded_id,
                        "similarity":similarity
                    }
                )
        
        similar_users = pd.DataFrame(similarityArr).sort_values(by="similarity",ascending=False)
        return similar_users[similar_users.similiar_users != item_input]
    except Exception as e:
        print("Error Occurs ",e)


###########################5. Get User Preference

def get_user_preferences(user_id,path_rating_df,path_df):
    
    rating_df = pd.read_csv(path_rating_df)
    df = pd.read_csv(path_df)
    

    animes_watched_by_user = rating_df[rating_df['user_id']== user_id]

    user_rating_percentile = np.percentile(animes_watched_by_user['rating'],75)

    animes_watched_by_user = animes_watched_by_user[animes_watched_by_user['rating'] >= user_rating_percentile]

    top_anime_user = (
        animes_watched_by_user.sort_values(by='rating',ascending=False).anime_id.values
    )

    anime_df_rows = df[df['MAL_ID'].isin(top_anime_user)]

    anime_df_rows = anime_df_rows[['eng_version','Genres']]


    return anime_df_rows

######################### 6. User Recommendataion

def get_user_recommendations(similar_users,user_preferences,path_df,path_synopsis_df,path_rating_df,n=10):

    recommended_animes = []
    anime_list =[]
    for user_id in similar_users['similiar_users'].values:
        # print("Similar User ID:",user_id)
        pref_list = get_user_preferences(int(user_id),path_rating_df,path_df)

        pref_list = pref_list[~pref_list['eng_version'].isin(user_preferences['eng_version'].values)]
       

        if not pref_list.empty:
            lists = pref_list['eng_version'].values
            anime_list.append(lists)

                    
    if anime_list:
        anime_list = pd.DataFrame(anime_list)

        sorted_list = pd.DataFrame(pd.Series(anime_list.values.ravel()).value_counts()).head(n)

        for i,anime_name in enumerate(sorted_list.index):

            n_user_pref = sorted_list[sorted_list.index == anime_name].values[0][0]

            if isinstance(anime_name,str):
                frame = getAnimeFrame(anime_name,path_df)
                
                anime_id = frame.MAL_ID.values[0]
              
                genre = frame.Genres.values[0]
                synopsis = getSypnopsis(int(anime_id),path_synopsis_df)
             
                recommended_animes.append(
                    {
                        "n" : n_user_pref,
                        "anime_name":anime_name,
                        "genre":genre,
                        "synopsis":synopsis
                    }
                )
    recommended_animes_df = pd.DataFrame(recommended_animes).head(n)
    return recommended_animes_df




