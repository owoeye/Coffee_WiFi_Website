from flask import Flask, url_for, render_template, redirect, session, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DecimalField
from wtforms.validators import DataRequired, URL
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
bootstrap = Bootstrap(app)

# secret key
app.config['SECRET_KEY'] = '2'

# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Cafe TABLE Configuration with SQL so it accessible in the code
class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class CafeForm(FlaskForm):
    cafe = StringField(label='Cafe Name', validators=[DataRequired()])
    location = StringField(label='Cafe Location', validators=[DataRequired()])
    map = StringField(label='Cafe Location on Google Maps (URL)', validators=[URL()])
    image = StringField(label='Cafe Image (URL)', validators=[URL()])
    sockets = SelectField(label='Are Power Sockets Available?', choices=["Yes", "No"])
    toilet = SelectField(label='Are Toilets Available?', choices=["Yes", "No"])
    wifi = SelectField(label='Is WiFi Available?', choices=["Yes", "No"])
    calls = SelectField(label='Do they have a Call Policy?', choices=["Yes", "No"])
    seats = SelectField(label='Seats Available', choices=["0-10", "10-20", "20-30", "30-40", "50+"])
    price = StringField(label='Coffee Price', validators=[DataRequired()])
    submit = SubmitField(label='Submit')


class Search(FlaskForm):
    category = SelectField(label='Search Category', choices=["Name", "Location", "Seats", "Toilet", "WiFi", "Sockets", "Caller Friendly", "Coffee Price"])
    cafe = StringField()
    search = SubmitField(label='Search')


def yes_no(value):
    if value:
        return "Yes"
    else:
        return "No"


# Flask routes for webpages
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/cafes")
def cafes():
    all_cafes = db.session.query(Cafe).all()
    all_cafes = [cafe.to_dict() for cafe in all_cafes]
    return render_template("cafes.html", cafes=all_cafes)


@app.route('/add', methods=["GET", "POST"])
def add_cafe():
    form = CafeForm()
    sent = False
    if form.validate_on_submit():
        # check if coffee shop is already in database
        name = form.cafe.data
        cafe_name = db.session.query(Cafe).filter_by(name=name).all()
        if not cafe_name:
            # add cafe to db
            new_cafe = Cafe(
                name=form.cafe.data.title(),
                map_url=form.map.data,
                img_url=form.image.data,
                location=form.location.data.title(),
                has_sockets=bool(form.sockets.data),
                has_toilet=bool(form.toilet.data),
                has_wifi=bool(form.wifi.data),
                can_take_calls=bool(form.calls.data),
                seats=form.seats.data,
                coffee_price=form.price.data,
            )
            db.session.add(new_cafe)
            db.session.commit()
            # sent acknowledgement check
            sent = True
        else:
            # if name is already in database acknowledge check
            sent = "exists"

    return render_template('add.html', form=form, sent=sent)


@app.route("/search", methods=["GET", "POST"])
def search():
    # create search bar
    search = Search()
    # search acknowledge message check
    response = False
    # check is button is clicked
    if search.validate_on_submit():
        # check what value is returned from the search
        cafe_location = False
        # fetch vale from search textbox
        value = search.cafe.data.title()
        # fetch category to search
        filter_param = search.category.data

        # list of possible categories
        filter_list = ["Name", "Location", "Seats", "Toilet", "WiFi", "Sockets", "Caller Friendly", "Coffee Price"]
        # search based of category if any value is in db and return none otherwise
        if filter_param == filter_list[0]:
            cafe_location = db.session.query(Cafe).filter_by(name=value).all()
        elif filter_param == filter_list[1]:
            cafe_location = db.session.query(Cafe).filter_by(location=value).all()
        elif filter_param == filter_list[2]:
            cafe_location = db.session.query(Cafe).filter_by(seats=value).all()
        elif filter_param == filter_list[3]:
            cafe_location = db.session.query(Cafe).filter_by(has_toilet=value).all()
        elif filter_param == filter_list[4]:
            cafe_location = db.session.query(Cafe).filter_by(has_wifi=value).all()
        elif filter_param == filter_list[5]:
            cafe_location = db.session.query(Cafe).filter_by(sockets=value).all()
        elif filter_param == filter_list[6]:
            cafe_location = db.session.query(Cafe).filter_by(can_take_calls=value).all()
        elif filter_param == filter_list[7]:
            cafe_location = db.session.query(Cafe).filter_by(coffee_price=value).all()

        # check if a value was returned
        if not cafe_location:
            response = True  # returns a response
        # redirect to show the cafes
        else:
            cafe_list = [cafe.to_dict() for cafe in cafe_location]
            print(cafe_list)
            return render_template('cafes.html', cafes=cafe_list)

    return render_template('search.html', search=search, response=response)


# HTTP PUT/PATCH - Update Record
@app.route("/edit", methods=["GET", "PATCH", "DELETE"])
def edit():
    name = request.args.get("name")
    cafe = db.session.query(Cafe).filter_by(name=name).first()

    form = CafeForm()
    form.cafe.data = cafe.name
    form.location.data = cafe.location
    form.map.data = cafe.map_url
    form.image.data = cafe.img_url
    form.sockets.data = yes_no(cafe.has_sockets)
    form.toilet.data = yes_no(cafe.has_toilet)
    form.wifi.data = yes_no(cafe.has_wifi)
    form.calls.data = yes_no(cafe.can_take_calls)
    form.seats.data = cafe.seats
    form.price.data = cafe.coffee_price

    if form.validate_on_submit():
        cafe.name = form.cafe.data.title()
        cafe.location = form.map.data
        cafe.img_url = form.image.data
        cafe.location = form.location.data.title()
        cafe.has_sockets = bool(form.sockets.data)
        cafe.has_toilet = bool(form.toilet.data)
        cafe.has_wifi = bool(form.wifi.data)
        cafe.can_take_calls = bool(form.calls.data)
        cafe.seats = form.seats.data
        cafe.coffee_price = form.price.data
        db.session.commit()

    return render_template("edit.html", form=form)


# HTTP DELETE - Delete Record
@app.route("/delete", methods=["GET", "DELETE"])
def delete():
    name = request.args.get("name")
    cafe = db.session.query(Cafe).filter_by(name=name).first()
    db.session.delete(cafe)
    db.session.commit()
    # print(name)
    return render_template("delete.html")


if __name__ == "__main__":
    app.run(debug=True)
