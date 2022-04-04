"""
Download historical game-level and season-level stats from barttorvik.com and store locally
(thanks Bart for making the site so download-friendly!)
"""

import datetime
from doctest import master
import json
import requests
import ssl

import pandas as pd

ssl._create_default_https_context = ssl._create_unverified_context


def save_game_stats():
    """
    get game-by-game adjusted offensive and defensive efficiency, 
    with each team having a record for each game
    """

    r = requests.get('https://barttorvik.com/getgamestats.php')
    json_data = json.loads(r.text)

    print("team-games found:", len(json_data))

    all_cols = ['date', 'del_1', 'team', 'conf', 'opp', 'location', 'result', 'adj_o', 'adj_d', 'o_ppp', 'o_efg', 'o_to', 'o_or', 'o_ftr', 'd_ppp', 'd_efg',
                'd_to', 'd_or', 'd_ftr', 'gsc', 'conf_opp', 'team_id', 'season', 'pace', 'game_id', 'coach', 'opp_coach', 'plus_minus', 'del_2', 'del_3', 'del_4']
    # data has no labels -> manually identified columns
    df = pd.DataFrame(json_data, columns=all_cols)

    save_cols = ['date', 'season', 'team', 'opp',
                 'location', 'adj_o', 'adj_d', 'o_ppp', 'd_ppp']
    # for now we only need efficiencies (absolute and maybe raw)
    df[save_cols].to_csv('../data/game_stats.csv', index=False)
    return


def save_season_stats():
    """get season stats (four factors and a few others) for each team in all available years"""

    end_year = get_current_year()
    years = range(2008, end_year+1)
    # note this always includes the current season

    master_team_stats = pd.DataFrame()
    for year in years:
        year_df = pd.read_csv(f'https://barttorvik.com/{year}_fffinal.csv')
        print(len(year_df), "teams found for", year)

        # raw columns are mismatched (first four are an index column, not labeled as such)
        year_df = year_df.reset_index()
        year_df.columns = list(
            year_df.columns[4:])+['blockrateD', 'rk.10', 'blockrateO', 'rk.11']

        # rank columns are not labeled -> add better labels
        for i in range(2, len(year_df.columns), 2):
            year_df.rename(
                columns={year_df.columns[i]: year_df.columns[i-1]+'_rk'}, inplace=True)

        year_df['season'] = year
        master_team_stats = master_team_stats.append(year_df)

    master_team_stats.to_csv('../data/team_stats.csv', index=False)


def save_pbp_stats():
    """get shooting splits for each team in all available years"""

    end_year = get_current_year()
    years = range(2010, end_year+1)
    # first year of pbp data is 2010
    # note this always includes the current season

    master_team_stats = pd.DataFrame()
    for year in years:
        year_df = pd.read_json(f'https://barttorvik.com/{year}_pbp_teamsstats.json')
        print(len(year_df), "team shooting splits found for", year)

        # syntax of response data: 'offense' : [close2_made, close2_missed, ??, long2_made long2_missed, ??, 3_made, 3_missed, ??]

        year_df['close2_pct'] = year_df['offense'].apply(lambda x: x[0]/(x[0]+x[1]))
        year_df['close2_share'] = year_df['offense'].apply(lambda x: (x[0]+x[1])/(x[0]+x[1]+x[3]+x[4]+x[6]+x[7]))
        
        year_df['long2_pct'] = year_df['offense'].apply(lambda x: x[3]/(x[3]+x[4]))
        year_df['long2_share'] = year_df['offense'].apply(lambda x: (x[3]+x[4])/(x[0]+x[1]+x[3]+x[4]+x[6]+x[7]))

        # threes are already in the team_stats data

        year_df['season'] = year
        year_df['team'] = year_df.index
        master_team_stats = master_team_stats.append(year_df).reset_index(drop=True)

    out_cols = ['season','team','close2_pct','close2_share','long2_pct','long2_share']
    master_team_stats[out_cols].to_csv('../data/pbp_stats.csv', index=False)
    return 


def save_season_efficiency():
    """get overall efficiency for each team in all available years"""

    end_year = get_current_year()
    years = range(2008, end_year+1)
    # note this always includes the current season

    efficiencies = pd.DataFrame()
    for year in years:
        year_df = pd.read_csv(f'http://barttorvik.com/{year}_team_results.csv')
        print(len(year_df), "team efficiencies found for", year)

        # raw columns are mismatched (first four are an index column, not labeled as such)
        year_df = year_df.reset_index()
        year_df.columns = list(
            year_df.columns[1:])+['tmp']

        year_df['season'] = year
        efficiencies = efficiencies.append(year_df).reset_index(drop=True)

    out_cols = ['season','team','adjoe','adjde']
    efficiencies[out_cols].to_csv('../data/team_efficiency.csv', index=False)
    return 
    

def get_current_year():
    """get the year corresponding to the current (or most recent) season"""
    
    today = datetime.date.today()
    return today.year if today.month < 11 else today.year + 1


def main():
    # save_game_stats()
    # save_season_stats()
    # save_pbp_stats()
    save_season_efficiency()


main()