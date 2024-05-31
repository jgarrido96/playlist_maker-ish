from flask import Flask, jsonify, request
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy import select, delete
from flask_sqlalchemy import SQLAlchemy
from marshmallow import fields, ValidationError
from flask_marshmallow import Marshmallow



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+mysqlconnector://root:itsyapassword69@localhost/playlist_manager"

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(app, model_class=Base)
ma = Marshmallow(app)



class Playlist(Base):
    __tablename__ = "playlist"
    playlist_id: Mapped[int] = mapped_column(primary_key=True)
    playlist_name: Mapped[str] = mapped_column(db.String(255), nullable=False)

class PlaylistSchema(ma.Schema):
    playlist_id = fields.Integer(required=False)
    playlist_name = fields.String(required=True)

    class Meta:
        fields = ('playlist_id', 'playlist_name')

playlist_schema = PlaylistSchema()
playlists_schema = PlaylistSchema(many=True)

# ====================== Playlist Actions ====================== #

@app.route('/')
def index():
    return '''
    Hello World!! Welcome to JDoggs playlist!!
    '''

@app.route('/playlist/create', methods = ['POST'])
def create_playlist():
    try:
        playlist_data = playlist_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    with Session(db.engine) as session:
        new_playlist = Playlist(playlist_name = playlist_data['playlist_name'])
        session.add(new_playlist)
        session.commit()
    return jsonify({'message': 'New Playlist Added Successfully'}), 201

@app.route('/playlist/view', methods = ['GET'])
def view_playlist():
    query = select(Playlist)
    result = db.session.execute(query).scalars()
    playlists = result.all()

    return playlists_schema.jsonify(playlists)

@app.route('/playlist/update/<int:id>', methods = ['PUT'])
def update_playlist(id):
    with Session(db.engine) as session:
        with session.begin():
            query = select(Playlist).filter(Playlist.playlist_id==id)
            result = session.execute(query).scalars().first()
            if result is None:
                return jsonify({"error": "Playlist Not Found"}), 404
            playlist = result

            try:
                playlist_data = playlist_schema.load(request.json)
            except ValidationError as e:
                return jsonify(e.messages), 400
            
            for field, value in playlist_data.items():
                # return f"for {field}, {value} in {playlist_data}"
                setattr(playlist, field, value)
            
            session.commit()
        return jsonify({"message": "Playlist Details Updated Successfully"}), 200

@app.route('/playlist/delete/<int:id>', methods = ['DELETE'])
def delete_playlist(id):
    delete_statement = delete(Playlist).where(Playlist.playlist_id==id)

    with db.session.begin():
        result = db.session.execute(delete_statement)

        if result.rowcount == 0:
            return jsonify({"error": "Playlist Not Found"}), 404
        
        return jsonify({"message": "Playlist Deleted Successfully"}), 200


class SongList(Base):
    __tablename__ = "song_list"
    songlist_id: Mapped[int] = mapped_column(primary_key=True)
    playlist_id: Mapped[int] = mapped_column(nullable=False)
    song_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    artist: Mapped[str] = mapped_column(db.String(255))

class SongSchema(ma.Schema):
    songlist_id = fields.Integer(required=False)
    playlist_id = fields.Integer(required=False)
    song_name = fields.String(required=True)
    artist = fields.String(required=False)

song_list_schema = SongSchema()
songs_list_schema = SongSchema(many=True)

# =================================== Song Actions ======================================= #

@app.route('/playlist/<int:id>/add_song', methods = ['POST'])
def add_a_song(id):
    try:
        song_data = song_list_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    with Session(db.engine) as session:
        new_song = SongList(playlist_id = id, song_name = song_data['song_name'], artist = song_data['artist'])
        session.add(new_song)
        session.commit()
    return jsonify({"message": "New Song Added Successfully!"}), 201

@app.route('/playlist/search', methods = ['GET'])
def search_songs():
    query = select(Playlist)
    result = db.session.execute(query).scalars()
    songs = result.all()
    
    return songs_list_schema.jsonify(songs)

# Deletes whole table :(
@app.route('/playlist/<int:pid>/remove_song/<int:sid>', methods = ['DELETE'])
def delete_song(pid, sid):
    delete_statement = delete(SongList).where(SongList.playlist_id==pid and SongList.songlist_id==sid)

    with db.session.begin():
        result = db.session.execute(delete_statement)

        if result.rowcount == 0:
            return jsonify({'error': "Song Not In Playlist"}), 404
        
        return jsonify({"message": "Song Deleted Successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)

