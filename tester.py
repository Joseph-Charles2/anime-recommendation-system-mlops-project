from utils.helpers import * 

from config.paths_config import * 

from pipeline.prediction_pipeline import hybrid_recommendation

# similar_user = find_similar_users(13994,USER_WEIGHTS_PATH,USER2USER_ENCODED,
#                        USER_ENCODED2USER,n=10,return_dist=False,neg=False)

# user_preference = get_user_preferences(11880,RATING_DF,DF)

# print(similar_user)
# print("**********************************************")
# print(user_preference)


print(hybrid_recommendation(13994))