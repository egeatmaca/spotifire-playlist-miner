from flask import Flask, render_template, request, redirect, url_for
from playlistminer import PlaylistMiner

app = Flask(__name__, template_folder='./static')

CLIENT_ID = 'YOUR-SPOTIFY-CLIENT-ID-HERE'
CLIENT_SECRET = 'YOUR-SPOTIFY-CLIENT-SECRET-HERE'

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
    app.run(debug=True)
    
