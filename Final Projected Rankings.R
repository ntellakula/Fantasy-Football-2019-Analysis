#required libraries
library(readxl)
library(janitor)
library(tidyverse)
library(directlabels)
library(ggrepel)
library(gridExtra)

#Importing the source and subsetting data to not show the team name
source <- read_excel("C:/Users/NTellaku/Documents/R/ff/Final Projected Rankings.xlsx",
                     sheet = "10 Guys One Cup")
no_team_name <- source %>% select(-Team)

#Fixing excel dates to R dates
fixed_dates <- excel_numeric_to_date(as.numeric(colnames(no_team_name)))
colnames(no_team_name) <- fixed_dates

#Extracting just the team names to have as a separate variable
name_column <- source %>% select(Team)

#Getting indices of Thursdays, and first date
th_index <- weekdays(fixed_dates) == "Thursday"
thursdays <- c(fixed_dates[1], fixed_dates[th_index])
analysis <- no_team_name[, as.character(thursdays)] %>% 
  bind_cols(name_column) %>% 
  select(Team, everything())


#convert the resulting list to a usable tibble
analysis_long <- analysis %>% 
  gather(Date, Rank, 2:ncol(analysis)) %>% 
  mutate(Date_fix = as.Date(Date)) %>% 
  arrange(Team) %>% 
  #adding before and after labels for the ggplot label
  mutate(label_max = if_else(Date == max(Date),
                             Team,
                             NA_character_)) %>% 
  mutate(label_min = if_else(Date == min(Date),
                             Team,
                             NA_character_))


#converting the whole list of dates to a usable tibble
full_dates_long <- source %>% 
  gather(Date, Rank, 2:ncol(no_team_name)) %>% 
  arrange(Team) %>% 
  mutate(Date_fix = str_sub(excel_numeric_to_date(as.numeric(Date)), 6, 10)) %>% 
  mutate(Date = excel_numeric_to_date(as.numeric(Date))) %>% 
  mutate(label_max = if_else(Date == max(Date),
                             Team,
                             NA_character_)) %>% 
  mutate(label_min = if_else(Date == min(Date),
                             Team,
                             NA_character_))



#draft day, max day
draft_day <- min(full_dates_long$Date)
maxim_day <- max(full_dates_long$Date)


#thursdays plot
plot_thu <- ggplot(analysis_long,
                   aes(x = Date_fix, y = Rank, group = Team, colour = Team)) +
  geom_line(size = 1) +
  scale_y_reverse(breaks = seq(1, 14, 1)) +
  scale_x_date(expand = c(0.05, 0.05)) +
  labs(x = "Date (Thursdays)",
       title = "ESPN Projected Rank by Week") +
  theme(panel.border = element_rect(colour = "black", fill = NA),
        plot.background = element_rect(fill = "white"),
        panel.background = element_rect(fill = "white"),
        panel.grid.major = element_line(size = 0.5, linetype = "solid",
                                        colour = "#ececec"),
        legend.position = "none") +
  geom_label_repel(aes(label = label_max),
                   nudge_x = 1,
                   na.rm = TRUE) +
  geom_label_repel(aes(label = label_min),
                   nudge_x = -1,
                   na.rm = TRUE)


#all dates plot
plot_full <- ggplot(full_dates_long,
                    aes(x = Date, y = Rank, group = Team, colour = Team)) +
  geom_line(size = 1) +
  scale_y_reverse(breaks = seq(1, 14, 1)) +
  scale_x_date(expand = c(0.05, 0.05),
               breaks = c(seq(draft_day, maxim_day, 7))) +
  labs(x = "Date",
       title = "ESPN Projected Rank by Day") +
  theme(panel.border = element_rect(colour = "black", fill = NA),
        plot.background = element_rect(fill = "white"),
        panel.background = element_rect(fill = "white"),
        panel.grid.major = element_line(size = 0.5, linetype = "solid",
                                        colour = "#ececec"),
        legend.position = "none") +
  geom_label_repel(aes(label = label_max),
                   nudge_x = 1,
                   na.rm = TRUE) +
  geom_label_repel(aes(label = label_min),
                   nudge_x = -1,
                   na.rm = TRUE)

#for a label in the middle of the line plot
direct.label(plot_full, "angled.boxes")
direct.label(plot_thu, "angled.boxes")


#creating a vector of team names
teams <- name_column %>% pull(Team)

#creating a vector of divergent colors
gg_color_hue <- function(n) {
  hues = seq(15, 375, length = n + 1)
  hcl(h = hues, l = 65, c = 100)[1:n]
}
colors <- gg_color_hue(10)

#initialize an empty list, then fill it with everyone's graph
#empty list of plots
graphs <- vector(mode = "list", length = length(teams))

for (i in 1:length(teams)) {
  graphs[[i]] <- ggplot() +
    geom_line(aes(x = Date,
                  y = Rank,
                  group = Team),
              data = full_dates_long,
              colour = alpha("grey", 0.6)) +
    geom_line(aes(x = Date,
                  y = Rank),
              data = full_dates_long %>% 
                filter(Team == teams[i]),
              size = 1,
              colour = colors[i]) +
    theme(panel.border = element_rect(colour = "black", fill = NA),
          plot.background = element_rect(fill = "white"),
          panel.background = element_rect(fill = "white"),
          legend.position = "none") +
    scale_y_reverse(breaks = seq(1, 14, 1),
                    expand = c(0.01,0.01)) +
    scale_x_date(breaks = c(seq(draft_day, maxim_day, 21)),
                 expand = c(0,0)) +
    labs(x = "Date",
         title = (teams[i]))
}

grid.arrange(graphs[[1]], graphs[[2]], graphs[[3]], graphs[[4]], graphs[[5]],
             graphs[[6]], graphs[[7]], graphs[[8]], graphs[[9]], graphs[[10]])


#Comparing first day and last day
source_cs <- source[, c(1, 2, length(source))] %>% 
  mutate(diff = `43804` - `43712`)
cor(source_cs %>% select(`43712`, `43804`), method = "kendall")
cor.test(source_cs$`43712`, source_cs$`43804`, method = "kendall")
