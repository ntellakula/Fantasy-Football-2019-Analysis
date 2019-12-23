# -*- coding: utf-8 -*-
"""
Created on Wed Oct  9 18:16:34 2019
"""

import requests
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

#league year and ID for data download
url = "https://fantasy.espn.com/apis/v3/games/ffl/seasons/2019/segments/0/leagues/298982"

#for historical
#url = "https://fantasy.espn.com/apis/v3/games/ffl/leagueHistory/" + str(league_id) + "?seasonId=" + str(year)
#if using historical year and not current year, change to r.json()[0]

#weekly matchups
r = requests.get(url, params = {"view": "mMatchup"})
d = r.json()

#figuring out how many weeks of material to pull, so no empty json
maximum = max(pd.DataFrame(d["schedule"]).index.tolist()) #how many obs?
length_df = pd.DataFrame([[d["schedule"][i]["winner"]] for i in range(maximum)])
#remove "undecided" game winners - weeks that have yet to be played
length_df = length_df[length_df[0] != "UNDECIDED"]
length = range(len(length_df)) #range for future loops for all games


#Selecting weeks, points, data
source = pd.DataFrame([[d["schedule"][i]["matchupPeriodId"],
                        d["schedule"][i]["home"]["teamId"],
                        d["schedule"][i]["home"]["totalPoints"],
                        d["schedule"][i]["away"]["teamId"],
                        d["schedule"][i]["away"]["totalPoints"]] for i in length],
                        columns = ["Week", "Team1", "Score1", "Team2", "Score2"])

#Create a list of each teams' margin of defeat/victory for each game
margins = source.assign(Margin1 = source["Score1"] - source["Score2"],
                        Margin2 = source["Score2"] - source["Score1"])

#team number to name Dictionary
mapping = {1: "Mount",
           2: "Alec",
           3: "Sirpi",
           4: "Oatman",
           5: "Babcock",
           9: "Jordan",
           11: "Casey",
           12: "Badillo",
           13: "Naki",
           14: "Kooper"}

#transpose from wide to long
margins_long = (margins[["Week", "Team1", "Margin1", "Score1"]]
                .rename(columns = {"Team1": "Team",
                                   "Margin1": "Margin",
                                   "Score1": "Score"})
                .append(margins[["Week", "Team2", "Margin2", "Score2"]]
                .rename(columns = {"Team2": "Team",
                                   "Margin2": "Margin",
                                   "Score2": "Score"})))

#add team name to the margins_long data frame
margins_long = (margins_long.assign(teamname = margins_long.Team)
                            .replace({"teamname": mapping}))

#creating record from values
team_ids = margins_long.Team.unique()

def team_win_loss(dataset, i):
    """
    Adding the win-loss record
    dataset: which dataset to use?
    i: iterator
    """
    team = dataset[dataset["Team"] == team_ids[i]]
    team_wins = sum(n > 0 for n in team["Margin"])
    team_ties = sum(n == 0 for n in team["Margin"])
    team_loss = sum(n < 0 for n in team["Margin"])
    points = np.sum(team.Score)
    wl_info = pd.DataFrame([[team_ids[i], team_wins, team_loss,
                             team_ties, points]],
                           columns = ["Team", "Wins", "Losses", "Ties",
                                      "Points"])
    return wl_info

#initialize an empty dataframe to append to
win_loss = []

#loop through all the teams and have the rows append
for j in range(len(team_ids)):
    row = team_win_loss(margins_long, j)
    win_loss.append(row)
win_loss = (pd.concat(win_loss)
              .sort_values(by = ["Wins", "Ties", "Points"], ascending = False)
              .assign(Standing = np.arange(1, 11))
              .reset_index(drop = True))
win_loss = (win_loss.assign(teamname = win_loss.Team,
                            Record = win_loss.Wins.map(str)
                                        + "-"
                                        + win_loss.Losses.map(str)
                                        + "-"
                                        + win_loss.Ties.map(str))
                    .replace({"teamname": mapping}))
########################## QED: Record and W/L ################################





##### Plot the Win/Loss Margins
fig, ax = plt.subplots(1, 1, figsize = (16, 6))
order = win_loss.teamname
sns.boxplot(x = "teamname", y = "Margin", data = margins_long, order = order)
ax.axhline(0, ls = "--")
ax.set_xlabel("")
ax.set_title("Win/Loss Margins")
plt.show()





##################################### Luck ####################################
#get the average of each week
averages = (margins.filter(["Week", "Score1", "Score2"])
                   .melt(id_vars = ["Week"],
                         value_name = "Score")
                   .groupby("Week")
                   .mean()
                   .reset_index())
                   
#initialize empty list
margin_average = []

for i in range(len(team_ids)):
    #select the team and corresponding owner name
    team = team_ids[i]
    team_owner = mapping[team]
    
    #create a dataframe for the score margin against team average per week
    df2 = (margins.query("Team1 == @team | Team2 == @team")
                  .reset_index(drop = True))
    #move df2 to have all team of interest into one column
    team_loc = list(df2["Team2"] == team)
    df2.loc[team_loc,
            ["Team1", "Score1",
             "Team2", "Score2"]] = df2.loc[team_loc, ["Team2", "Score2",
                                                      "Team1", "Score1"]].values
    #Add new score and win columns
    df2 = (df2.assign(change1 = df2["Score1"] - averages["Score"],
                  change2 = df2["Score2"] - averages["Score"],
                  Win = df2["Score1"] > df2["Score2"]))
    
    #Append it to the end
    margin_average.append(df2)

#remove the useless initiator row
margin_average = pd.concat(margin_average)

#limits to plot against: max and min of margins
marg_max = max(margin_average.iloc[:, [7, 8]].max(axis = 1))
marg_min = min(margin_average.iloc[:, [7, 8]].min(axis = 1))
plot_limit = max(marg_max, np.abs(marg_min))

#now make it into a graphic
x_fill = np.arange(0.0, plot_limit + 1, 0.01)
y_fill = np.arange(0.0, plot_limit + 1, 0.01)
x_negf = np.arange((plot_limit +1) * -1, 0, 0.01)
y_negf = np.arange((plot_limit +1) * -1, 0, 0.01)

def luck_graphic(index):
    #Index is team number
    team = team_ids[index]
    team_owner = mapping[team]
    team_rec = (win_loss[win_loss.Team == team].Record
                                               .to_string(index = False)
                                               .strip())
    
    #pull the necessary data
    graph_data = margin_average[margin_average.Team1 == team]
        
    ax = sns.scatterplot(x = "change1", y = "change2", data = graph_data,
                     style = "Win")
    plt.title("Team " + str(team_owner) + " Scores (Centered at Weekly League Average)\nRecord: " + team_rec)
    #plt.title("Team Mount Scores (Centered at Weekly League Average)")
    plt.ylim(-(plot_limit + 1), plot_limit + 1)
    plt.xlim(-(plot_limit + 1), plot_limit + 1)
    ax.spines["left"].set_position("zero")
    ax.spines["bottom"].set_position("zero")
    ax.spines['right'].set_color("none")
    ax.spines['top'].set_color("none")
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.fill_between(x_fill, 0, y_fill, color = "blue", alpha = 0.2)
    ax.fill_between(y_fill, x_fill, plot_limit + 1, color = "red", alpha = 0.2)
    ax.fill_between(x_negf, 0, y_negf, color = "red", alpha = 0.2)
    ax.fill_between(y_negf, x_negf, -(plot_limit + 1), color = "blue",
                    alpha = 0.2)
    ax.plot([-(plot_limit + 1), plot_limit + 1],
            [-(plot_limit + 1), plot_limit + 1],
            color = "black",
            linestyle = "-.")
    ax.text(-(plot_limit * .16), (plot_limit * 0.8), "Points\nAgainst",
            color = "black", size = "medium",
            horizontalalignment = "center", style = "italic")
    ax.text((plot_limit * 0.9), -(plot_limit * .25), "Points\nFor",
            color = "black", size = "medium",
            horizontalalignment = "center", style = "italic")
    ax.text((plot_limit * .16), (plot_limit * 0.8), "Unlucky\nLoss",
            color = "red", size = "medium",
            horizontalalignment = "center", style = "italic")
    ax.text(-(plot_limit * .16), -(plot_limit * 0.9), "Lucky\nWin",
            color = "blue", size = "medium",
            horizontalalignment = "center", style = "italic")
    ax.text((plot_limit * 0.9), (plot_limit * .25), "Good\nWin",
            color = "blue", size = "medium",
            horizontalalignment = "center", style = "italic")
    ax.text(-(plot_limit * .9), -(plot_limit * 0.16), "Bad\nLoss",
            color = "red", size = "medium",
            horizontalalignment = "center", style = "italic")







########### Making a Heat Map - Each Team Against One Another #################
def weekly_aggregate(i):
    """
    subset all scores by a given week then add record, wins, scores
    """
    #all the scores for the week, sorted, and adding columns for the w/l/t
    scores = (margins_long[margins_long.Week == (i + 1)]
                .sort_values(by = ["Score"])
                .reset_index(drop = True)
                .assign(total_wins = np.arange(0, len(team_ids), 1),
                        total_loss = np.arange(len(team_ids) - 1, -1, -1),
                        ind = np.arange(0, len(team_ids), 1)))
    
    #which values have matching scores?
    ties_loc = np.argwhere(np.array(scores.duplicated(subset = "Score",
                                                      keep = False)) == True)
    
    #split the duplicated and non-duplicated values into separate DFs
    scores_nod = (scores[~scores.total_wins.isin(ties_loc.flatten())]
                    .assign(total_ties = 0))
    scores_dup = scores[scores.total_wins.isin(ties_loc.flatten())]
    
    #what are the unique scores in the list of duplicates?
    unique_scores = scores_dup.Score.unique()
    
    #only run through the loop if there are duplicates
    if len(unique_scores) > 0:
        #loop through all the scores to add the ties
        #initiate list
        dup_list = []
        for j in range(len(unique_scores)):
            
            #iterating through all the repeated scores
            unique = scores[scores.Score == unique_scores[j]]
            
            #add in loss/wins
            unique.total_wins = min(unique.total_wins)
            unique.total_loss = min(unique.total_loss)
            unique = unique.assign(total_ties = len(team_ids) - 1
                                   - (unique.total_loss + unique.total_wins))
            
            dup_list.append(unique)
            
        #compile them
        dup_list = pd.concat(dup_list)
        dup_list = pd.concat([dup_list, scores_nod]).sort_values(by = ["ind"])
        return dup_list
    
    else:
        scores["total_ties"] = 0
        return scores

#initialize an empty dataframe to append to
full_wl = []
    
#loop through all the teams and have the rows append
for j in range(13):
    row = weekly_aggregate(j)
    full_wl.append(row)
    
#remove the first row which was just empty
full_wl = pd.concat(full_wl)

#combining for one row per team
sum_scores = (full_wl.groupby("Team")
                     .sum()
                     .drop("Week", axis = 1)
                     .sort_values(by = "total_loss"))
sum_scores = sum_scores.assign(record = sum_scores.total_wins.map(str)
                                        + "-"
                                        + sum_scores.total_loss.map(str)
                                        + "-"
                                        + sum_scores.total_ties.map(str))
####################### QED for against everyone simulation ###################





################### Combine win_loss & sum_scores #############################
#win_loss = win_loss.assign(Order = np.arange(1, 11, 1))
analysis = (sum_scores.assign(Team3 = sum_scores.index.tolist(),
                              Team2 = sum_scores.index.tolist(),
                              order = np.arange(1, 11, 1))
                      .replace({"Team2": mapping})
                      .merge(win_loss, how = "left", left_on = "Team2",
                             right_on = "teamname"))
analysis = (analysis[["Team2", "Points", "record", "Record"]]
            .assign(Difference = analysis["Standing"] - analysis["order"])
            .rename(columns = {"Team2": "Owner",
                               "record": "Simulated Record",
                               "Record": "ESPN Record"}))
    
#dataset to tranpose week by week wins
colnames = "Week " + pd.Series(full_wl.Week.unique()).map(str)
wins_pivot = full_wl.pivot(index = "Team", columns = "Week",
                           values = "total_wins")
loss_pivot = full_wl.pivot(index = "Team", columns = "Week",
                           values = "total_loss")
ties_pivot = full_wl.pivot(index = "Team", columns = "Week",
                           values = "total_ties")
wins_pivot.columns = colnames
loss_pivot.columns = colnames
ties_pivot.columns = colnames

#append each individual week's record
pivoted_record = []
for i in range(0, wins_pivot.shape[1]):
    old_name = "Week " + str(i + 1)
    var_name = "Record " + str(i + 1)
    pivoted_record.append(pd.DataFrame(wins_pivot.iloc[:, i].map(str)
                                        + "-"
                                        + loss_pivot.iloc[:, i].map(str)
                                        + "-"
                                        + ties_pivot.iloc[:, i].map(str))
                            .rename(columns = {old_name: var_name}))
pivoted_record = pd.concat(pivoted_record, axis = 1)

    
#merge analysis with all the wins, then the actual records. then create 2 blanks of 4.5 for heatmap
final_analysis = (analysis.merge(wins_pivot.assign(teamnum = wins_pivot.index.tolist())
                                            .replace({"teamnum": mapping}), how = "left",
                                                                            left_on = "Owner",
                                                                            right_on = "teamnum")
                          .drop("teamnum", axis = 1)
                          .merge(pivoted_record.assign(teamnum = pivoted_record.index.tolist())
                                               .replace({"teamnum": mapping}), how = "left",
                                                                               left_on = "Owner",
                                                                               right_on = "teamnum")
                          .set_index("Owner")
                          .drop("teamnum", axis = 1)
                          .assign(blank_sr = np.full_like(wins_pivot,
                                                          (len(team_ids) - 1) / 2,
                                                          dtype = np.double)[:, 1],
                                  blank_er = np.full_like(wins_pivot,
                                                          (len(team_ids) - 1) / 2,
                                                          dtype = np.double)[:, 1]))

#final data set is analysis to make into a heat plot
#red to green
cmap = sns.diverging_palette(10, 150, n = 9, as_cmap = True)

#editing the differences to show up in the heatmap and agree with colors
diff = pd.DataFrame(final_analysis.Difference)
diff[diff > 0] = len(team_ids) - 1
diff[diff == 0] = (len(team_ids) - 1) / 2
diff[diff < 0] = 0


num_weeks = max(full_wl.Week)
analysis_hm = (final_analysis.iloc[:, 4:(4 + num_weeks)]
                              .assign(Simulated = final_analysis.blank_sr,
                                      ESPN = final_analysis.blank_er,
                                      Difference = diff))
analysis_hm_labels = (final_analysis.iloc[:, len(final_analysis.columns)
                         - (num_weeks + 2):len(final_analysis.columns) - 2]
                                    .assign(sim_record = final_analysis["Simulated Record"],
                                            esp_record = final_analysis["ESPN Record"],
                                            Difference = final_analysis.Difference))

#make the plot
plt.figure(figsize = (num_weeks * 2, 7))
sns.heatmap(analysis_hm, cmap = cmap, annot = analysis_hm_labels,
            cbar = False, fmt = "", linewidth = 0.5)
plt.title("Simulated vs ESPN Records by Week & Total")
################################# QED Heatmap #################################









############################### Line Plots ####################################
#import the raw data
source = pd.read_excel("C:/Users/NTellaku/Documents/R/ff/Final Projected Rankings.xlsx",
              sheet_name = "10 Guys One Cup")

#remove team name and transpose, then apply the team names as column names
source_noteam = source.iloc[:, 1:]
team_names = source.Team
source_t = pd.DataFrame(source_noteam.T)
source_t.columns = team_names


column_dates = list(source.columns.values)[1:]
#putting dates in mm-dd-yy format
dates_fixed = [d.strftime("%m-%d-%y") for d in column_dates]

#Initialize the figure
plt.style.use("seaborn-dark-palette")
plt.figure(figsize = (15, 15))

#Create a color palette
palette = plt.get_cmap("tab10")

#Multiple Line Plot
num = 0 #iterator
for column in source_t:
    num += 1
    
    #Correct spot in the plot
    plt.subplot(len(team_ids) / 2, 2, num)
    
    #plot every group, but discrete
    for v in source_t:
        plt.plot(column_dates,
                 source_t[v],
                 marker = "",
                 linewidth = 0.7,
                 alpha = 0.2,
                 color = "grey")
        
       
    #Plot the actual lineplot
    color = palette(num - 1)
    
    plt.plot(column_dates,
             source_t[column],
             marker = "",
             color = color,#palette(num - 1),
             linewidth = 2.4,
             alpha = 0.9,
             label = column)
        
    #Same limits for everybody
    plt.ylim(0.5, len(team_ids) + 0.5)
    plt.xlim(column_dates[0], column_dates[-1])
    
    #Specifying ticks and tick locations
    if num in range(len(team_names) + 1) :
        t = [dates_fixed[0],
             dates_fixed[round(len(dates_fixed) / 2)],
             dates_fixed[-1]]
        plt.xticks(t, t)
    if num in range(len(team_names) - 1):
        plt.tick_params(labelbottom = "off")
        
    s = [1, 5, 10]
    plt.yticks(s, s)
        
    #Add a title
    plt.title(column, loc = "left", fontsize = 12,
              fontweight = 0, color = color)#palette(num - 1))
    plt.gca().invert_yaxis()

    
#General title
plt.suptitle("ESPN Final Projected Ranking by Day",
             fontsize = 13,
             fontweight = 0,
             color = "black",
             style = "italic")






################################ Alternative W/L ##############################
#removing Week 13: selection Week
ml2 = margins_long[margins_long.Week != 13]

#finding win/loss records at the end of Week 12, or end of reg season
#initiate empty list
wl2 = []

#loop through all the teams and have the rows append
for j in range(len(team_ids)):
    row = team_win_loss(ml2, j)
    wl2.append(row)
wl2 = (pd.concat(wl2)
              .sort_values(by = ["Wins", "Ties", "Points"], ascending = False)
              .assign(Standing = np.arange(1, 11))
              .reset_index(drop = True))
wl2 = (wl2.assign(teamname = wl2.Team,
                  Record = wl2.Wins.map(str)
                      + "-"
                      + wl2.Losses.map(str)
                      + "-"
                      + wl2.Ties.map(str))
            .replace({"teamname": mapping}))

#remove week 13 from the averages
av2 = averages[averages.Week != 13]

#initiate empty list
against_averages = []

#loop through the teams, and calculate wins against weekly average
for i in range(len(team_ids)):
    num = team_ids[i]
    raw = (ml2[ml2.Team == num].sort_values(by = ["Week"])
                               .merge(av2,
                                      how = "right",
                                      left_on = "Week",
                                      right_on = "Week"))
    raw = raw.assign(add_win = np.where(raw.Score_x > raw.Score_y, 1, 0),
                     add_loss = np.where(raw.Score_x < raw.Score_y, 1, 0),
                     add_tie = np.where(raw.Score_x == raw.Score_y, 1, 0))
    against_averages.append(raw)
    
ag_av = (pd.concat(against_averages).groupby("Team")
                                    .sum()
                                    .drop(["Week", "Margin",
                                           "Score_x", "Score_y"], axis = 1))

#adding in OG record with W/L against average record
alt_record = wl2.merge(ag_av.assign(TeamNum = ag_av.index),
                       how = "left", left_on = "Team", right_on = "TeamNum")
alt_record = alt_record.assign(alt_wins = alt_record.Wins + alt_record.add_win,
                               alt_loss = alt_record.Losses + alt_record.add_loss,
                               alt_ties = alt_record.Ties + alt_record.add_tie)
alt_record["Alt_Record"] = (alt_record.alt_wins.map(str)
                                        + "-"
                                        + alt_record.alt_loss.map(str)
                                        + "-"
                                        + alt_record.alt_ties.map(str))
final_alt = (alt_record.sort_values(by = ["alt_wins", "alt_ties", "Points"],
                                    ascending = False)
                       .assign(new_Standing = np.arange(1,
                                                        len(team_ids) + 1, 1)))
#final variable selection
alt_analysis = final_alt[["Standing", "new_Standing", "teamname", "Points",
                          "Record", "Alt_Record"]]





##################### Alternate Records - Include Week 13 ######################initiate empty list
against_averages2 = []

#loop through the teams, and calculate wins against weekly average
for i in range(len(team_ids)):
    num = team_ids[i]
    raw = (margins_long[margins_long.Team == num].sort_values(by = ["Week"])
                               .merge(averages,
                                      how = "right",
                                      left_on = "Week",
                                      right_on = "Week"))
    raw = raw.assign(add_win = np.where(raw.Score_x > raw.Score_y, 1, 0),
                     add_loss = np.where(raw.Score_x < raw.Score_y, 1, 0),
                     add_tie = np.where(raw.Score_x == raw.Score_y, 1, 0))
    against_averages2.append(raw)
    
ag_av2 = (pd.concat(against_averages2).groupby("Team")
                                      .sum()
                                      .drop(["Week", "Margin",
                                             "Score_x", "Score_y"], axis = 1))
    
#add in team names
ag_av2 = ag_av2.assign(teamname = ag_av2.index).replace({"teamname": mapping})