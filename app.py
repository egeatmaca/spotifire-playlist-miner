from flask import Flask, render_template, request, redirect, url_for
from playlistminer import PlaylistMiner
import os

app = Flask(__name__, template_folder='./static')

CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return render_template('index.html')
    elif request.method == 'POST':
        keywords = request.form['keywords']
        playlist_title = f'''Your {
            ' '.join([word[0].upper()+word[1:].lower() for word in keywords.split()])
        } Playlist:'''
        playlist = PlaylistMiner(CLIENT_ID, CLIENT_SECRET).make_playlist(keywords)
        return render_template('index.html', playlist_title=playlist_title, playlist=playlist)
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
