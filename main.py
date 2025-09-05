from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os


API_KEY = os.environ.get("API_KEY")
url = "https://api.themoviedb.org/3/search/movie"
detail_url = "https://api.themoviedb.org/3/movie"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
Bootstrap(app)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///movie-collection.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(500), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f"<Data id: {self.id} | title: {self.title} | year: {self.year} | description: {self.description} | rating: {self.rating} | rank: {self.ranking} | review; {self.review} | url: {self.img_url}"
with app.app_context():
    db.create_all()
    db.session.commit()
    # if not Movie.query.filter_by(title="Phone Booth").first():
    #     new_movie = Movie(
    #         title="Phone Booth",
    #         year=2002,
    #         description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
    #         rating=7.3,
    #         ranking=10,
    #         review="My favourite character was the caller.",
    #         img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
    #     )
    #     db.session.add(new_movie)
    #     db.session.commit()
    # else:
    #     print("added")

class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5", validators=[DataRequired()])
    review = StringField("Your Review", validators=[DataRequired()])
    submit = SubmitField("Done")

class AddMovie(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")

@app.route("/")
def home():

    movie = Movie.query.order_by(Movie.rating.desc()).all()
    for i, m in enumerate(movie):
        m.ranking = i+1
    # movies = Movie.query.all()
    return render_template("index.html", movies=movie)


@app.route("/edit", methods=["POST", "GET"])
def edit():
    form = RateMovieForm()
    if form.validate_on_submit():
        id = request.args.get("id")
        movie = Movie.query.get(id)
        movie.rating = form.rating.data
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))

    id = request.args.get("id")
    return render_template("edit.html", form=form, id=id)

@app.route("/delete")
def delete():
    id = request.args.get("id")
    movie = Movie.query.get(id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/add", methods=["POST", "GET"])
def add():
    form = AddMovie()
    if form.validate_on_submit():
        header = {
            "api_key": API_KEY,
            "query": form.title.data
        }
        response = requests.get(url, params=header)
        data = response.json()
        movies = data["results"]
        return render_template("select.html", movies=movies)
    return render_template("add.html", form=form)

@app.route("/select")
def add_select():
    id = request.args.get("id", type=int)
    param = {
        "api_key": API_KEY
    }
    response = requests.get(f"{detail_url}/{id}", params=param)
    data = response.json()
    if not Movie.query.filter_by(title=data["title"]).first():
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            description=data["overview"],
            img_url=f"https://image.tmdb.org/t/p/w500{data["poster_path"]}"
        )
        db.session.add(new_movie)
        db.session.commit()
        movie = Movie.query.filter_by(title=data["title"]).first()
        id = movie.id
        return redirect(url_for("edit", id=id))
    form = AddMovie()
    return redirect("add")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
