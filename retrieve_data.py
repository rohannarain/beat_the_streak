import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsapi
import json
import re
import datetime

from tqdm import tqdm
from collections import OrderedDict

import sys
import argparse

################################################## GLOBAL VARIABLES ###############################################################

yesterday = (datetime.datetime.today() - datetime.timedelta(days = 1)).strftime("%m/%d/%Y")
today = datetime.datetime.today().strftime("%m/%d/%Y")

################################################## UTILITY/GETTER FUNCTIONS #######################################################

def get_player_list(team_id):
    """
    A function that gets a list of every player (including pitchers) a given team.
    
    Parameters 
    -----–-----------
    team_id: int
        The team ID number (i.e. 137 for S.F. Giants)
    """
    player_names = []
    roster = statsapi.roster(team_id)
    roster_list = roster.split("\n")[:-1]
    for player in roster_list:
        player_names.append(" ".join(player.split()[2:]))
    return player_names

def get_player_id_from_name(player_name):
    """
    A function that gets the player ID for a name entered in any 
    format (Last, First; First Last; Last, etc.).
    
    Parameters 
    -----–-----------
    player_name: str
        The name of a player as a string (i.e. "Buster Posey")
    """
    try:
        return statsapi.lookup_player(player_name)[0]['id']
    except IndexError:
        return False

def check_pos_player(player_name):
    """
    A function that returns a bool indicating whether or not the player
    is a position player (as opposed to a pitcher).
    
    Parameters 
    -----–-----------
    player_name: str
        The name of a player as a string (i.e. "Buster Posey")
    """
    try:
        return statsapi.lookup_player(player_name)[0]['primaryPosition']['abbreviation'] != "P"
    except IndexError:
        return False

def get_current_season_stats(player_name):
    """
    One of the main data retrieval functions. Returns a dictionary 
    mapping the names of different statistics to the values of those
    statistics. Only includes overall season statistics for the player
    passed in. 
    
    Parameters 
    -----–-----------
    player_name: str
        The name of a player as a string (i.e. "Buster Posey")
    """

    if not check_pos_player(player_name):
        raise ValueError("Player name entered is not a position player")
        
    player_id = get_player_id_from_name(player_name)
    stats_dict = OrderedDict({"Name": player_name, "ID": player_id, 
                  "Team": statsapi.lookup_player(player_id)[0]['currentTeam']['id']})
    
    # Look up the player's current season hitting stats
    get_player_stats = statsapi.player_stats(player_id, 'hitting') 
    
    # Get the stats for the most recent season
    curr_season_stats = get_player_stats.split("Season Hitting")[-1]
    
    #Break up the stats into a list
    stats_list = curr_season_stats.split("\n")[1:-2]
    for stat in stats_list:
        stat_name = re.search("[A-Za-z]+", stat).group()
        
        # Temporary fix for a bug that appeared 8/20/2019.
        if stat_name == 'flyOuts':
            continue
            
        stat_val = re.search("[^:A-Za-z]+", stat).group()
        try:
            stats_dict[stat_name] = float(stat_val)
        except ValueError:
            stats_dict[stat_name] = 0.0
    return stats_dict


# These functions were defined with the help of toddrob99 on github, who developed the
# MLB-StatsAPI module. I made a post on reddit.com/r/mlbdata, which he mantains to 
# answer questions about making API calls for specific purposes. I asked how to get stats
# over the past x days and how to get head-to-head batting stats. The post is linked
# here: https://www.reddit.com/r/mlbdata/comments/cewwfo/getting_headtohead_batting_stats_and_last_x_games/?

def get_h2h_vs_pitcher(batter_id, opponent_id):
    """
    Returns a dictionary containing a limited amount of head-to-head batting 
    statistics between the hitter (batter_id) and pitcher (opponent_id) 
    specified. One of the main data retrieval functions.
    
    Parameters 
    -----–-----------
    batter_id: int
        The 6-digit ID of a batter, which can be fetched using 
        get_player_id_from_name('Hitter Name').
    
    opponent_id: int
        The 6-digit ID of a pitcher, which can be fetched using 
        get_player_id_from_name('Pitcher Name').
    """
    
    hydrate = 'stats(group=[hitting],type=[vsPlayer],opposingPlayerId={},season=2019,sportId=1)'.format(opponent_id)
    params = {'personId': batter_id, 'hydrate':hydrate, 'sportId':1}
    r = statsapi.get('person',params)
    
    # Look up batting stats versus pitcher, if atBats_h2h == 0 return 
    # a dictionary of empty stats.
    try: 
        batting_stats = r['people'][0]['stats'][1]['splits'][0]['stat']
    except KeyError:
        return OrderedDict({'atBats_h2h': 0.0, 'avg_h2h': 0.0, 'hits_h2h': 0.0, 
                            'obp_h2h': 0.0, 'ops_h2h': 0.0, 'slg_h2h': 0.0})
    
    # Only get rate stats vs pitcher
    filtered = {(k + "_h2h"):(float(v) if v != "-.--" and v != ".---" and v != "*.**" else 0.0)
                for k, v in batting_stats.items() 
                if type(v) == str 
                and k != 'stolenBasePercentage'
                and k != 'atBatsPerHomeRun'
                or k == 'hits'
                or k == 'atBats'} 
    
    # Making sure the keys are in the same order regardless of players entered
    filtered = OrderedDict(sorted(filtered.items()))
    
    return filtered

def batting_past_N_games(N, player_id):  
    """
    Returns a dictionary containing a limited amount of batting statistics 
    over the past N games for a specified player. One of the main data retrieval 
    functions.
    
    Parameters 
    -----–-----------
    N: int
        Specifies how many games back to look for batting statistics.
    
    player_id: int
        The 6-digit ID of a hitter, which can be fetched using 
        get_player_id_from_name('Hitter Name').
    """
    
    hydrate = 'stats(group=[hitting],type=[lastXGames],limit={}),currentTeam'.format(N)
    params = {'personId': player_id, 'hydrate':hydrate}
    
    # Attempt to look up stats over the past N games, and if nothing comes
    # up, return a list of stats containing only 0.0. 
    try:
        r = statsapi.get('person',params)
        batting_stats = r['people'][0]['stats'][0]['splits'][0]['stat']
    except (ValueError, KeyError):
        return {k:v for k, v in (zip(np.arange(5), [0.0]*5))}
    
    # Only get rate stats for past N games
    filtered = {k + "_p{}G".format(N):(float(v) if v != "-.--" and v != ".---" and v != "*.**" else 0.0)
                for k, v in batting_stats.items() 
                if type(v) == str 
                and k != 'stolenBasePercentage'
                or k == 'hits'} 
    
    # Preserving order across players
    filtered = OrderedDict(sorted(filtered.items()))
    
    return filtered

def pitching_past_N_games(N, player_id):
    """
    Returns a dictionary containing a limited amount of pitching statistics 
    over the past N games for a specified player. One of the main data retrieval 
    functions.
    
    Parameters 
    -----–-----------
    N: int
        Specifies how many games back to look for pitching statistics.
    
    player_id: int
        The 6-digit ID of a pitcher, which can be fetched using 
        get_player_id_from_name('Pitcher Name').
    """
    
    # Jose Abreu's (1B) name gets looked up if you pass in 
    # an empty string to statsapi.lookup_player().
    if player_id == 547989:
        return {k:v for k, v in (zip(np.arange(15), [0.0]*15))}
    
    hydrate = 'stats(group=[pitching],type=[lastXGames],limit={}),currentTeam'.format(N)
    params = {'personId': player_id, 'hydrate':hydrate}
    
    try:
        r = statsapi.get('person',params)
    except ValueError:  # The request fails if a pitcher is making their debut
        return {k:v for k, v in (zip(np.arange(15), [0.0]*15))}
    
    pitching_stats = r['people'][0]['stats'][0]['splits'][0]['stat']
    
    # Only get rate stats for past N days
    filtered = {(k + "_p{}G".format(N)):(float(v) if v != "-.--" and v != ".---" and v != "*.**" else 0.0)
                for k, v in pitching_stats.items() 
                if type(v) == str} 
    
    # Preserving order across players
    filtered = OrderedDict(sorted(filtered.items()))
    
    return filtered

def check_pitcher_right_handed(pitcher_id):
    """
    Returns a bool indicating whether a pitcher is right handed.

    Parameters 
    -----–-----------
    pitcher_id: int
        The 6-digit ID of a pitcher, which can be fetched using 
        get_player_id_from_name('Pitcher Name').        
    """
    try:
        params = {'personId': pitcher_id}
        r = statsapi.get('person',params)
        return r['people'][0]['pitchHand']['code'] == 'R'
    except IndexError:
        return True # Most pitchers are righties

def check_batter_right_handed(batter_id):
    """
    Returns a bool indicating whether a hitter is right handed.

    Parameters 
    -----–-----------
    batter_id: int
        The 6-digit ID of a batter, which can be fetched using 
        get_player_id_from_name('Hitter Name').        
    """
    try:
        params = {'personId': batter_id}
        r = statsapi.get('person',params)
        return r['people'][0]['batSide']['code'] == 'R'
    except IndexError:
        return True # Most batters are righties

def check_pitcher_batter_opposite_hand(batter_id, pitcher_id):
    """
    Returns a bool indicating whether a batter and pitcher 
    have opposite handedness.

    Parameters 
    -----–-----------
    batter_id: int
        The 6-digit ID of a batter, which can be fetched using 
        get_player_id_from_name('Hitter Name').      
        
    pitcher_id: int
        The 6-digit ID of a pitcher, which can be fetched using 
        get_player_id_from_name('Pitcher Name'). 
    """
    return check_pitcher_right_handed(pitcher_id) != check_batter_right_handed(batter_id)

def player_got_hit_in_game(player_id, game_id, home_or_away):
    """
    This function generates labels for training data. Checks if a 
    player got a hit in a specified game. 

    Parameters 
    -----–-----------
    player: int
        The 6-digit ID of a batter, which can be fetched using 
        get_player_id_from_name('Hitter Name').      
        
    game_id: int
        The 6-digit ID for a game, can be fetched from statsapi.schedule().
    
    home_or_away: bool
        Indicates whether the player was on the home team or the 
        away team for the specified game.
    """
    
    params = {'gamePk':game_id,
      'fields': 'gameData,teams,teamName,shortName,teamStats,batting,atBats,runs,hits,rbi,strikeOuts,baseOnBalls,leftOnBase,players,boxscoreName,liveData,boxscore,teams,players,id,fullName,batting,avg,ops,era,battingOrder,info,title,fieldList,note,label,value'}
    r = statsapi.get('game', params)
    player_stats = r['liveData']['boxscore']['teams'][home_or_away]['players'].get('ID' + str(player_id), False)
    if not player_stats: 
        return False 
    else:
        return player_stats['stats']['batting'].get('hits', 0) > 0

def convert_to_FL_format(name):
    """
    Takes the name of a player in Last, First format and converts
    it to First Last format. 

    Parameters 
    -----–-----------
    name: str
        The name of a player in Last, First format.  
    """
    last_first = name.split(",")
    last_first.reverse()
    last_first[0] = last_first[0].strip()
    return " ".join(last_first)


################################################## FUNCTION TO GENERATE DATA #######################################################

def generate_hits_data(generate_train_data=True):
    """
    Main data retrieval function. Combines all other functions defined
    above and generates data either for training or testing. Produces
    a dataframe and writes it to a CSV, putting it in the data/player_stats
    directory like so:
    
        data/player_stats/player_stats_08_20_2019.csv
    
    The date at the end of the file name changes depending on the value
    passed for generate_train_data.

    Parameters 
    -----–-----------
    generate_train_data: bool
        Indicates whether the function should generate training or test
        data. Simply changes which day's games to look at. 
    """

    ###############################################################
    # 
    # Change GENERATE_TRAIN_DATA to False to generate 
    # data for today's games instead, which won't have 
    # labels included for whether or not the player
    # got a hit
    #
    GENERATE_TRAIN_DATA = generate_train_data
    #
    ################################################################

    gameday = yesterday
    if not GENERATE_TRAIN_DATA:
        gameday = today

    rows_list = []
    for game in tqdm(statsapi.schedule(gameday)):

        game_id = game['game_id']
        away_id = game['away_id']
        home_id = game['home_id']
        home_player_list = get_player_list(home_id)
        away_player_list = get_player_list(away_id)

        away_prob_Pname = convert_to_FL_format(game['away_probable_pitcher'])
        home_prob_Pname = convert_to_FL_format(game['home_probable_pitcher'])

        away_probable_pitcher = get_player_id_from_name(away_prob_Pname)
        home_probable_pitcher = get_player_id_from_name(home_prob_Pname)

        away_pitcher_p5G = pitching_past_N_games(5, away_probable_pitcher)
        home_pitcher_p5G = pitching_past_N_games(5, home_probable_pitcher)

        for player in home_player_list:
            player_id = get_player_id_from_name(player)
            try:
                new_row = list(get_current_season_stats(player).values())
                new_row += list(batting_past_N_games(7, player_id).values())
                new_row += list(batting_past_N_games(15, player_id).values())
                new_row += list(away_pitcher_p5G.values())
                new_row += list(get_h2h_vs_pitcher(player_id, away_probable_pitcher).values())
                new_row.append(float(check_pitcher_batter_opposite_hand(batter_id=player_id, 
                                                                      pitcher_id=away_probable_pitcher)))
                if GENERATE_TRAIN_DATA:
                    new_row.append(player_got_hit_in_game(player_id, game_id, 'home'))

                rows_list.append(new_row)
            except (ValueError, IndexError):
                continue

        for player in away_player_list:
            player_id = get_player_id_from_name(player)
            try:
                new_row = list(get_current_season_stats(player).values())
                new_row += list(batting_past_N_games(7, player_id).values())
                new_row += list(batting_past_N_games(15, player_id).values())
                new_row += list(home_pitcher_p5G.values())
                new_row += list(get_h2h_vs_pitcher(player_id, home_probable_pitcher).values())
                new_row.append(float(check_pitcher_batter_opposite_hand(batter_id=player_id, 
                                                                      pitcher_id=away_probable_pitcher)))
                if GENERATE_TRAIN_DATA:
                    new_row.append(player_got_hit_in_game(player_id, game_id, 'away'))

                rows_list.append(new_row)
            except (ValueError, IndexError):
                continue
        
    sample_hitter = get_player_id_from_name("Kevin Pillar")
    sample_pitcher = get_player_id_from_name("Jacob DeGrom")
    player_stats_columns = list(get_current_season_stats("Kevin Pillar").keys())
    player_stats_columns += list(batting_past_N_games(7, sample_hitter).keys())
    player_stats_columns += list(batting_past_N_games(15, sample_hitter).keys())
    player_stats_columns += list(pitching_past_N_games(5, sample_pitcher).keys())
    player_stats_columns += list(get_h2h_vs_pitcher(sample_hitter, sample_pitcher).keys())

    if GENERATE_TRAIN_DATA:
        player_stats_columns += ['pitcher_hitter_opposite_hand', 'player_got_hit']
    else:
        player_stats_columns += ['pitcher_hitter_opposite_hand']

    player_stats_table = pd.DataFrame(data=rows_list, columns=player_stats_columns)
    file_to_generate = "data/player_stats/player_stats_{}.csv".format(gameday.replace("/", "_"))
    player_stats_table.to_csv(file_to_generate, index=False)
    print("Finished generating file: {}".format(file_to_generate))
    
def generate_yesterdays_results():
    """
    Generates tables to put on the Past Results page for project 
    website. Puts the tables in the data/past_results directory.  
    """
    
    pred_yest = pd.read_csv("data/predictions/predictions_{}.csv".format(yesterday.replace("/", "_")))
    stats_yest = pd.read_csv("data/player_stats/player_stats_{}.csv".format(yesterday.replace("/", "_")))
    
    past_results = stats_yest[stats_yest['Name'].isin(pred_yest['Name'])].loc[:, ['Name', 'player_got_hit']]
    past_results['player_got_hit'] = past_results['player_got_hit'].apply(lambda x: "Yes" if x == 1.0 else "No")
    past_results = past_results.append({'Name': 'Overall Accuracy', 
                                        'player_got_hit': sum(past_results['player_got_hit'] == 'Yes') / 10}, 
                                       ignore_index=True)
    
    past_results.to_csv("data/past_results/past_results_{}.csv".format(yesterday.replace("/", "_")), index=False)
    print("Results for {} generated".format(yesterday))

# Adding arguments for running from command line or in .sh script. 

arg_parser = argparse.ArgumentParser(description="Run to generate training data from yesterday's games and test data from today's games")
arg_parser.add_argument("--train", help = "Use if you want to generate training data only", action="store_true")
arg_parser.add_argument("--test", help = "Use if you want to generate test data only", action="store_true")
args = arg_parser.parse_args()

if args.train:
    generate_hits_data()
elif args.test:
    generate_hits_data(generate_train_data=False)
else:
    generate_hits_data()
    generate_hits_data(generate_train_data=False)
    generate_yesterdays_results()
    