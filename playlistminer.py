import numpy as np
import pandas as pd
import spotify
import asyncio
from prefixspan import PrefixSpan

class PlaylistMiner:
    def __init__(self, client_id, client_secret):
        self.data = []
        self.client = spotify.Client(client_id, client_secret)
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError as ex:
            if "There is no current event loop in thread" in str(ex):
                print('Creating new event loop...')
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                self.loop = asyncio.get_event_loop()

    def make_playlist(self, keywords):
        self.get_data(keywords)
        self.prep_data()
        self.mine_sequences()
        self.merge_mined_sequences()
        self.decode_playlist()
        return self.playlist
         
    def get_data(self, keywords):
        self.loop.run_until_complete(self.search_playlists(keywords))
        for playlist in self.search_results.playlists:
            self.loop.run_until_complete(self.get_playlist_tracks(playlist))
        return self.data
    
    async def search_playlists(self, keywords):
        self.keywords = keywords
        self.search_results = await self.client.search(q=keywords, types=['playlist'], limit=50)

    async def get_playlist_tracks(self, playlist):
        try:
            self.data.append(await playlist.get_all_tracks())
        except:
            pass

    def prep_data(self):
        self.data_preped = []
        self.track_lookup = pd.DataFrame(columns=['id', 'spotify_id', 'artist', 'track'])
        id_counter = 0
        for playlist in self.data:
            playlist_preped = []
            for track in playlist:
                if (track.id == self.track_lookup.spotify_id).sum() > 0:
                    playlist_preped.append(
                        int(self.track_lookup.loc[self.track_lookup.spotify_id == track.id, 'id'])
                    )
                else:
                    self.track_lookup = pd.concat([
                        self.track_lookup,
                        pd.DataFrame(
                            [[id_counter, track.id, track.artist.name, track.name]], 
                            columns=self.track_lookup.columns
                        )
                    ])
                    playlist_preped.append(id_counter)
                    id_counter += 1
            self.data_preped.append(playlist_preped)
        return self.data_preped

    def mine_sequences(self):
        ps = PrefixSpan(self.data_preped)
        self.freq_sequences = ps.topk(k=20, closed=True, filter=lambda patt, matches: len(patt)>3)
        return self.freq_sequences

    def merge_mined_sequences(self):
        freq_sequences = pd.DataFrame(self.freq_sequences, columns=['sup', 'seq'])
        freq_sequences['subseq'] = freq_sequences.seq.apply(
            lambda seq: self.is_subsequence_of_any(seq, freq_sequences.seq)
        )
        freq_sequences = freq_sequences.loc[freq_sequences.subseq==False, ['sup', 'seq']]
        freq_sequences['first_item'] = freq_sequences.seq.apply(lambda seq: seq[0])
        freq_sequences = freq_sequences.sort_values(['sup', 'first_item']).reset_index(drop=True)
        
        playlist = []
        ends_with = None
        idx_to_add = []
        while len(idx_to_add)>0 or (len(playlist)<20 and freq_sequences.shape[0]>0):
            if len(idx_to_add)>0:
                idx_to_add = idx_to_add[0]
                playlist += list(freq_sequences.loc[idx_to_add, 'seq'])[1:]
            else:
                idx_to_add = freq_sequences.index[0]
                playlist += list(freq_sequences.loc[idx_to_add, 'seq'])
            playlist = pd.Series(playlist).drop_duplicates().tolist()
            freq_sequences = freq_sequences.drop(index=idx_to_add)
            ends_with = playlist[-1]
            idx_to_add = freq_sequences.loc[freq_sequences.seq.apply(lambda seq: seq[0])==ends_with, 'seq'].index
        self.playlist_encoded = playlist
        return self.playlist_encoded

    def decode_playlist(self):
        self.playlist = pd.Series(self.playlist_encoded).apply(
            lambda id: ' - '.join(
                self.track_lookup.loc[self.track_lookup.id==id, ['artist', 'track']].values.tolist()[0]
            )
        ).tolist()
        return self.playlist
        
    def is_subsequence_of(self, subsequence, supersequence):
        subsequence = pd.Series(subsequence)
        supersequence = pd.Series(supersequence)
        for element in subsequence:
            positions = np.where(supersequence==element)[0]
            if positions.shape[0] > 0:
                supersequence = supersequence[positions[0]:]
            else:
                return False
        return True

    def is_subsequence_of_any(self, subsequence, supersequences):
        subsequence = pd.Series(subsequence)
        supersequences = pd.Series(supersequences)
        return supersequences.apply(
            lambda supersequence: self.is_subsequence_of(subsequence, supersequence) and not (
                len(subsequence)==len(supersequence) and (subsequence==supersequence).all())
        ).any()
         

def test(keywords='hiphop'):
    CLIENT_ID = 'YOUR-SPOTIFY-CLIENT-ID-HERE'
    CLIENT_SECRET = 'YOUR-SPOTIFY-CLIENT-SECRET-HERE'
    
    plm = PlaylistMiner(CLIENT_ID, CLIENT_SECRET)
    plm.make_playlist(keywords)
    print(plm.playlist)
    return plm
