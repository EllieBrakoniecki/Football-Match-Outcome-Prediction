import pandas as pd
import os
import numpy as np
import pickle
import seaborn as sns
import matplotlib.pyplot as plt
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath('__file__')))
DATA_DIR = os.path.join(BASE_DIR, 'feature_eng', 'data', 'ft_df.csv')
MODEL_DIR = os.path.join(BASE_DIR, 'heroku', 'models')
df = pd.read_csv(DATA_DIR)
df.head()

df.shape
(6077, 50)
df.info()


df.describe().round(2)

#checking class proportions
class_p = (df.winner.value_counts(normalize = True) *100).round(2).reset_index()
class_p.columns = ['winner', '%']
class_p


#checking class proportions
class_p = (df.ls_winner.value_counts(normalize = True) *100).round(2).reset_index()
class_p.columns = ['winner', '%']
class_p

# We can see that most of the times the home team wins, which is common knowledge in the soccer community.

# Also we have more than 70% of the dataframe containing winning data, that's one of the reasons why it's going to be difficult to predict draws.

df['date'] = pd.to_datetime(df.date)

num_cols = df.dtypes[df.dtypes != 'object'].index.tolist()


#creating dummy dependent variables and set of columns to check their correlation with the dependent variables

cols_to_drop = ['season', 'match_name','date', 'home_team', 'away_team', 'home_score', 'away_score',
                'h_match_points', 'a_match_points']

corr_cols = list(set(num_cols) - set(cols_to_drop))

df['winner_h'] = np.where(df.winner == 'HOME_TEAM', 1, 0)
df['winner_a'] = np.where(df.winner == 'AWAY_TEAM', 1, 0)
df['winner_d'] = np.where(df.winner == 'DRAW', 1, 0)
df[corr_cols + ['winner_h']].corr()['winner_h'].sort_values(ascending = False).reset_index()



df[corr_cols + ['winner_a']].corr()['winner_a'].sort_values(ascending = False).reset_index()


df[corr_cols + ['winner_d']].corr()['winner_d'].sort_values(ascending = False).reset_index()

# By checking these correlation dataframes we can see that when one of the two teams wins, the features that seem to have the highest correlation are those that say how the teams are ranked in the current and last season and the teams odds.

# We can also see that the weighted exponential average also has a higher correlation to the dependent variables than the regular metrics.

# We can observe that there isn't much correlation of the variables to the draw outcome. Which means that we'll probably have a hard time trying to predict the draw outcome.

# Understanding RFE features
# Here we'll use the selected features in the modeling phase, chosen through RFE method, and try and understand them better.

model = pickle.load(open(os.path.join(MODEL_DIR, "lr_model.pkl"), 'rb'))
model['features']

color = sns.color_palette("CMRmap")

sns.set(rc={'figure.figsize':(20,20)}, palette = color, style = 'white')


for i, column in enumerate(model['features'], 1):
    try:
        plt.subplot(5,2,i)
        sns.histplot(df[column]).set(ylabel = None)
        sns.despine(left=True)
    except:
        pass
    
    # In the histograms shown above we can see that the features aren't normally distributed and are also in different scales, that's why we applied the MinMaxScaler transformation in the modeling phase.
    
    color = sns.color_palette("CMRmap")

sns.set(palette = color, style = 'white', font_scale = 2)

g = sns.pairplot(df[['h_odd',
 'd_odd',
 'a_odd',
 'ht_rank',
 'ht_l_points',
 'at_rank',
 'at_l_points',
 'at_l_wavg_points',
 'at_l_wavg_goals',
 'at_l_wavg_goals_sf',
 'at_win_streak']])



for ax in g.axes.flatten():
    ax.xaxis.label.set_rotation(90)
    ax.yaxis.label.set_rotation(0)
    ax.yaxis.labelpad = 100   
    
    
In this pairplot we can observe some linearities:

The w.e.a. points has a positive correlation with the w.e.a. goals metric and a negative correlation with the w.e.a. goals suffered metric, which makes perfect sense. If a teams makes more points it's going to score more goals and suffer less goals.

The home team odd goes up as the w.e.a. points and goals of the away team also goes up. Which means that the more the away team scores, the less the chance of the home team wins.

The draw odd is also sort of correlated to the both teams odd, probably because every game is gonna have a team with a higher odd, and the draw odd tends to be near the higher odd.

We can also see some obvious linearities, like the home team odd going down as the away team rank goes up. Which means that the lowest the away team's position in the table, the higher the chance of the home team winning.

