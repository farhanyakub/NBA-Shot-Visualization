from flask import Flask, render_template, jsonify, request, send_file
from flask_mysql_connector import MySQL
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Arc
import seaborn as sns
from io import BytesIO
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config['MYSQL_USER'] = os.getenv('USERNAME')
app.config['MYSQL_DATABASE'] = os.getenv('DATABASE')
app.config['MYSQL_PASSWORD'] = os.getenv('PASSWORD')
app.config['MYSQL_HOST'] = os.getenv('HOST')
mysql = MySQL(app)

SHOTX = []
SHOTY = []
PLAYERNAME = ''
SEASON = ''

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/getAllPlayers', methods=['GET'])
def getPlayers():
    cur = mysql.new_cursor(dictionary=True)
    cur.execute('''SELECT * FROM player''')
    output = cur.fetchall()
    return jsonify(output)

@app.route('/getPlayerInfo', methods=['POST'])
def getPlayerInfo():
    data = request.get_json()
    playerName = data['player']
    cur = mysql.new_cursor(dictionary=True)
    query = f'''SELECT * FROM player JOIN shots USING(playerID) JOIN team USING(teamID) WHERE playerName = %s'''
    cur.execute(query, (playerName,))
    output = cur.fetchall()
    teams = []
    for team in output:
        if team['teamName'] in teams:
            continue
        else:
            teams.append(team['teamName'])
    return jsonify(teams)

@app.route('/query', methods=['POST'])
def getQuery():
    data = request.get_json()
    playerName = data['player']
    teamName = data['team']
    location = data['location']
    season = data['season']
    shottype = data['shottype']
    shotmade = data['shotmade']
    time = data['time']
    cur = mysql.new_cursor(dictionary=True)
    query = f'''SELECT shotX, shotY FROM player JOIN shots USING(playerID) JOIN team USING(teamID) JOIN time USING(shotID)
                WHERE playerName = %s AND teamName = %s AND time <= %s AND season = %s'''
    if location == 'home':
        query += ' AND homeTeam = TRUE'
    elif location == 'away':
        query += ' AND homeTeam = FALSE'
    
    if shottype == '2':
        query += ' AND shotType = 2'
    elif shottype == '3':
        query += ' AND shotType = 3'
    
    if shotmade == 'made':
        query += ' AND made = TRUE'
    elif shotmade == 'missed':
        query += ' AND made = FALSE'
    
    cur.execute(query, (playerName, teamName, time, season,))
    output = cur.fetchall()
    if output == []:
        return jsonify({"message" : "Error"}), 200
    
    global SHOTX, SHOTY, PLAYERNAME, SEASON
    SHOTX = np.array([coord['shotX'] for coord in output])
    SHOTY = np.array([coord['shotY'] for coord in output])
    PLAYERNAME = playerName.title()
    SEASON = season
    return jsonify({"message" : "Success"}), 200

@app.route('/get_scatter')
def get_scatter():
    global SHOTX, SHOTY, PLAYERNAME, SEASON
    fig, ax = plt.subplots(figsize=(9, 9))
    draw_nba_court(ax)
    ax.scatter(
        x=(SHOTX * 10) - 250,
        y=SHOTY * (422.5 / 47),
        alpha=0.2,
        s=15,
        color='red'
    )
    plt.title(f"{PLAYERNAME} {SEASON} chart")
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return send_file(buf, mimetype='image/png'), 200

@app.route('/get_heatmap')
def get_heatmap():
    global SHOTX, SHOTY, PLAYERNAME, SEASON
    fig, ax = plt.subplots(figsize=(9, 9))
    draw_nba_court(ax)
    kde = sns.kdeplot(
        x = (np.array(SHOTX) * 10) - 250, # adjust for coordinates of plot
        y = np.array(SHOTY) * (422.5 / 47.5), # adjust for coordinates of plot
        fill = True,
        cmap = 'plasma',
        bw_adjust = 0.8,
        alpha = 0.6,
        levels = 100, 
        thresh = 0.05,
        ax = ax
    )
    plt.title(f"{PLAYERNAME} {SEASON} chart")
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return send_file(buf, mimetype='image/png'), 200


# Taken from a youtube video but understand what's happening
def draw_nba_court(axis=None):
    if axis is None:
        fig = plt.figure(figsize=(9, 9))
        axis = fig.add_subplot(111, aspect='auto')
    else:
        fig = None

    # --- Court Outline (Baseline, Sidelines, Halfcourt Line) ---
    axis.plot([-250, 250], [-47.5, -47.5], 'k-')     # Baseline
    axis.plot([-250, -250], [-47.5, 422.5], 'k-')    # Left sideline
    axis.plot([250, 250], [-47.5, 422.5], 'k-')      # Right sideline
    axis.plot([-250, 250], [422.5, 422.5], 'k-')     # Halfcourt line

    # --- Backboard ---
    axis.plot([-30, 30], [-10, -10], 'k-', lw=2)

    # --- Paint / Lane ---
    axis.plot([-80, -80], [-47.5, 142.5], 'k-')
    axis.plot([80, 80], [-47.5, 142.5], 'k-')
    axis.plot([-60, -60], [-47.5, 142.5], 'k-')
    axis.plot([60, 60], [-47.5, 142.5], 'k-')
    axis.plot([-80, 80], [142.5, 142.5], 'k-')     # Free throw line

    # --- Hoop and Restricted Area ---
    hoop = Arc((0, 0), 15, 15, theta1=0, theta2=360, lw=1.5, color='black')
    restricted = Arc((0, 0), 80, 80, theta1=0, theta2=180, lw=1.5, color='black')
    axis.add_patch(hoop)
    axis.add_patch(restricted)

    # --- Free Throw Circle ---
    axis.add_patch(Arc((0, 142.5), 120, 120, theta1=0, theta2=180, lw=1.5, color='black'))     # Top half
    axis.add_patch(Arc((0, 142.5), 120, 120, theta1=180, theta2=360, lw=1.5, linestyle='--', color='black'))  # Bottom half (dashed)

    # --- 3-Point Lines ---
    axis.plot([-220, -220], [-47.5, 92.5], 'k-')     # Left corner 3
    axis.plot([220, 220], [-47.5, 92.5], 'k-')       # Right corner 3
    axis.add_patch(Arc((0, 0), 475, 475, theta1=22, theta2=158, lw=1.5, color='black'))   # 3-pt arc

    # --- Halfcourt Circle ---
    axis.add_patch(Arc((0, 422.5), 122, 122, theta1=180, theta2=360, lw=1.5, color='black'))

    # --- Axis Settings ---
    axis.set_xlim(-250, 250)
    axis.set_ylim(-47.5, 470)
    axis.set_aspect(1)     # Equal aspect ratio
    axis.axis('off')       # Hide axes

    return fig, axis


if __name__ == '__main__':
    app.run(debug=True)


# Do i need a header?
# if yes then what's on it
#   - Title of site, maybe a logo with a basketball hoop?
# Then go into explaining what the website is and what it's about
#   - maybe allow a certain number of comparisons to be done with shot charts
# Need search bar for players (not required) and then touchdown bars for all other query based searches
# Can improve by highlighting percentage of shots taken in area but that can be for another day