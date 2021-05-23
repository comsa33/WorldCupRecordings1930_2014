import pandas as pd
import sqlite3

csv_files = ['WorldCupMatches.csv', 'WorldCupPlayers.csv', 'WorldCups.csv']
dfs = []
for i, f in enumerate(csv_files):
    globals()['df_{}'.format(i)] = pd.read_csv(f, encoding='latin-1', engine='python')
    dfs.append(globals()['df_{}'.format(i)])
    new_cols = []
    for col in globals()['df_{}'.format(i)].columns:
        col = col.replace(' ', '')
        col = col.replace('-','_')
        new_cols.append(col)
    print(new_cols)
    globals()['df_{}'.format(i)].columns = new_cols
    print(globals()['df_{}'.format(i)].columns)

dfs[0].dropna(axis=0, how='all', inplace=True)
dfs[0]["match_index"] = dfs[0].index
dfs[0]['Datetime'] = dfs[0]['Datetime'].apply(lambda x: x.replace('June', 'Jun'))

id_cnt = 0
matchID = "1096"
match_index = []
for i in range(37784):
    if matchID == str(dfs[1]['MatchID'][i]):
        match_index.append(str(id_cnt))
        matchID = str(dfs[1]['MatchID'][i])
    else:
        id_cnt += 1
        match_index.append(str(id_cnt))
        matchID = str(dfs[1]['MatchID'][i])

dfs[1]['match_index'] = match_index
print(dfs[1])

con = sqlite3.connect('WorldCup.db')
cursor = con.cursor()
for i in range(3):
    dfs[i].to_sql(csv_files[i][:-4], con, if_exists='replace')


import sys
import threading
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QStandardItem
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView as QWebView,QWebEnginePage as QWebPage
from PyQt5.QtWebEngineWidgets import QWebEngineSettings as QWebSettings
from PyQt5 import QtGui
from PyQt5 import uic

form_class = uic.loadUiType("worldcup.ui")[0]

class WorldCupApp(QMainWindow, form_class):

    con = sqlite3.connect('WorldCup.db')
    cursor = con.cursor()

    # cursor.execute("""SELECT M.Datetime, M.Stage, M.Stadium, M.City,
    #                          M.HomeTeamName, M.AwayTeamName, P.PlayerName, P.Position, P.Event
    #                          FROM WorldCupMatches M, WorldCupPlayers P
    #                          WHERE M.match_index = P.match_index order by M.match_index""")

    # print(cursor.fetchone())

    df_matches = pd.read_sql("SELECT * FROM WorldCupMatches", con, index_col='index')
    df_players = pd.read_sql("SELECT * FROM WorldCupPlayers", con, index_col='index')
    df_wc = pd.read_sql("SELECT * FROM WorldCups", con, index_col='index')
    df_m_p = pd.read_sql("""SELECT M.Datetime, M.Stage, P.CoachName,
                             P.PlayerName, P.TeamInitials, P.Line_up, P.ShirtNumber, P.Position, P.Event
                             FROM WorldCupMatches M, WorldCupPlayers P
                             WHERE M.match_index = P.match_index order by M.match_index""", con)
    print(df_matches.info())
    print(df_m_p.columns)
    print(df_matches.columns)
    print(df_players.columns)
    df_matches = df_matches.astype({'Year': 'str', 'HomeTeamGoals': 'str', 'AwayTeamGoals': 'str'})

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.initUI()
        self.WcYears = list(set(self.df_matches['Year'].values))
        self.fill_list_year()
        self.listWidget.clicked.connect(self.showDatetime)
        self.listWidget_2.clicked.connect(self.showMatchInfo)

        self.home_players.clicked.connect(lambda: self.showPlayerInfo(self.df_home_players, 'home'))
        self.away_players.clicked.connect(lambda: self.showPlayerInfo(self.df_away_players, 'away'))

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.webview = QWebView(self)
        self.layout.addWidget(self.webview)
        self.home_browser.setLayout(self.layout)

        self.layout_2 = QVBoxLayout()
        self.layout_2.setContentsMargins(0, 0, 0, 0)
        self.webview_2 = QWebView(self)
        self.layout_2.addWidget(self.webview_2)
        self.away_browser.setLayout(self.layout_2)


    def clearContentsAll(self):
        self.stadium.clear()
        self.city.clear()
        self.home_init.clear()
        self.away_init.clear()
        self.home_goals.clear()
        self.away_goals.clear()
        self.home_players.clear()
        self.away_players.clear()
        self.home_name.setText("HOME PLAYERS")
        self.away_name.setText("AWAY PLAYERS")
        self.referee.setText("[Referee] / [Assistants]")
        self.home_coach.setText("-")
        self.away_coach.setText("-")
        self.player_no.setText("-")
        self.player_pos.setText("-")
        self.player_lineup.setText("-")
        self.player_event.clear()
        self.player_no_2.setText("-")
        self.player_pos_2.setText("-")
        self.player_lineup_2.setText("-")
        self.player_event_2.clear()
        self.webview.setUrl(QUrl("https://www.google.com/"))
        self.webview_2.setUrl(QUrl("https://www.google.com/"))

    def showDatetime(self):
        self.clearContentsAll()
        self.listWidget_2.clear()
        selected_year = self.listWidget.currentItem().text()
        result_df = self.df_matches[self.df_matches['Year'].str.contains(selected_year, na=False)]
        print(result_df['Datetime'])
        Datetimes = result_df['Datetime'].values
        Stages = result_df['Stage'].values
        for i in range(len(Datetimes)):
            self.listWidget_2.addItem(str(Datetimes[i]+" - "+Stages[i]))

    def showMatchInfo(self):
        self.clearContentsAll()
        selected_date_stage = self.listWidget_2.currentItem().text()
        selected_date = selected_date_stage[:19]
        selected_stage = selected_date_stage[23:]
        print(selected_date, selected_stage)
        cond_1 = self.df_matches['Datetime'].str.contains(selected_date, na=False)
        cond_2 = self.df_matches['Stage'].str.contains(selected_stage, na=False)
        cond_1_p = self.df_m_p['Datetime'].str.contains(selected_date, na=False)
        cond_2_p = self.df_m_p['Stage'].str.contains(selected_stage, na=False)
        result_df_m = self.df_matches[cond_1 & cond_2]
        result_df_p = self.df_m_p[cond_1_p & cond_2_p]
        self.applyMatchInfo(result_df_m)
        self.applyPlayersInfo(result_df_p)

    def applyMatchInfo(self, result_df_m):
        print(result_df_m.columns)
        print(result_df_m.values)
        self.home_init.setText(result_df_m.values[0][-3])
        self.away_init.setText(result_df_m.values[0][-2])
        self.home_goals.setText(result_df_m.values[0][6][0])
        self.away_goals.setText(result_df_m.values[0][7][0])
        self.stadium.setText(result_df_m.values[0][3])
        self.city.setText(result_df_m.values[0][4])
        self.referee.setText("[Referee] "+ result_df_m.values[0][-8] +
                             " / [Assistants] "+ result_df_m.values[0][-7] +
                             ", " + result_df_m.values[0][-6])
        self.home_name.setText(result_df_m.values[0][5]+" PLAYERS")
        self.away_name.setText(result_df_m.values[0][8]+" PLAYERS")

    def applyPlayersInfo(self, result_df_p):
        self.home_players.clear()
        self.away_players.clear()
        print(result_df_p.columns)
        print(result_df_p.values)
        self.df_home_players = result_df_p[result_df_p['TeamInitials'] == self.home_init.text()]
        self.df_away_players = result_df_p[result_df_p['TeamInitials'] == self.away_init.text()]
        print(self.df_away_players['PlayerName'].values)
        for name in self.df_home_players['PlayerName'].values:
            item = QListWidgetItem(name)
            item.setTextAlignment(Qt.AlignRight)
            self.home_players.addItem(item)
        for name in self.df_away_players['PlayerName'].values:
            self.away_players.addItem(name)
        print(self.df_home_players['CoachName'].values[0])
        self.home_coach.setText("[COACH] : "+str(self.df_home_players['CoachName'].values[0]))
        self.away_coach.setText("[COACH] : "+str(self.df_away_players['CoachName'].values[0]))
        self.home_players.clicked.connect(lambda: self.showPlayerInfo(self.df_home_players, 'home'))
        self.away_players.clicked.connect(lambda: self.showPlayerInfo(self.df_away_players, 'away'))

    def showPlayerInfo(self, df_players, team):
        param = "&hl=en&gl=ar&tbm=isch&sxsrf=ALeKk00r2mDgU_sgWQMyNj-93OwXfAUwgQ%3A1621703699311&source=hp&ei=EzypYOLbEPLVmAX3wLLYDA&oq=&gs_lcp=ChJtb2JpbGUtZ3dzLXdpei1pbWcQARgAMgcIIxDqAhAnMgcIIxDqAhAnMgcIIxDqAhAnMgcIIxDqAhAnMgcIIxDqAhAnUABYAGDJGmgBcAB4AIABAIgBAJIBAJgBALABBQ&sclient=mobile-gws-wiz-img"
        if team == 'home':
            selected_player = self.home_players.currentItem().text()
            df_selected_player = df_players[df_players['PlayerName'] == selected_player]
            self.player_no.setText(str(df_selected_player.values[0][-3])+" 번")
            self.player_pos.setText(str(df_selected_player.values[0][-2]))
            self.player_lineup.setText(str(df_selected_player.values[0][-4]))
            self.player_event.setText(str(df_selected_player.values[0][-1]))
            self.webview.setUrl(QUrl("https://www.google.com/search?q=soccer+"+selected_player.replace(' ', '+')+param))
        elif team == 'away':
            selected_player = self.away_players.currentItem().text()
            df_selected_player = df_players[df_players['PlayerName'] == selected_player]
            self.player_no_2.setText(str(df_selected_player.values[0][-3]) + " 번")
            self.player_pos_2.setText(str(df_selected_player.values[0][-2]))
            self.player_lineup_2.setText(str(df_selected_player.values[0][-4]))
            self.player_event_2.setText(str(df_selected_player.values[0][-1]))
            self.webview_2.setUrl(QUrl("https://www.google.com/search?q=soccer+"+selected_player.replace(' ', '+')+param))

    def fill_list_year(self):
        self.WcYears.sort()
        for year in self.WcYears:
            item = QListWidgetItem(str(year)[:-2])
            item.setTextAlignment(Qt.AlignCenter)
            self.listWidget.addItem(item)

    def initUI(self):
        self.setWindowTitle('WORLD CUP 1930-2014')
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = WorldCupApp()
    form.show()
    exit(app.exec_())