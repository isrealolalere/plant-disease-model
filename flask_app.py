from flask import Flask, request, render_template, redirect, url_for
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array, load_img
import numpy as np
import io
import os


from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length
from flask_sqlalchemy  import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

import sqlite3 as sql

# Load the model
model = load_model('Maize_InceptionV3_model.keras')

app = Flask(__name__)
app.config['SECRET_KEY'] = '66a616d076cd4976ca2754564333rrtre'

# Define the labels and testing directory
data_labels = ['Blight', 'Common_rust', 'Gray_leaf_spot', 'Healthy']


@app.route('/')
@login_required
def index():
    return render_template('index.html')

def preprocess_image(image):
    # Example: Resize to 224x224, change according to your model's requirements
    image = image.resize((224, 224))
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)
    image = image / 255.0  # Normalize if needed
    return image




# @app.route('/predict', methods=['POST'])
# def predict():
#     if 'file' not in request.files:
#         return redirect(url_for('index'))
    
#     file = request.files['file']

#     if file.filename == '':
#         return redirect(url_for('index'))
    
#     if file and file.filename.lower().endswith(('png', 'jpg', 'jpeg')):
#         # Load the image and preprocess it
#         img = load_img(io.BytesIO(file.read()), target_size=(224, 224))
#         img = preprocess_image(img)

#         # Make prediction
#         prediction = model.predict(img)
#         predicted_label = data_labels[np.argmax(prediction, axis=1)[0]]
#         probability = np.max(prediction)  # Get the highest probability

#         # Render the result page with all necessary information
#         return render_template('result.html', 
#                                pred=predicted_label, 
#                                prob=f"{probability:.2f}")
    
#     return redirect(url_for('index'))




from werkzeug.utils import secure_filename

@app.route('/predict', methods=['POST'])
@login_required
def predict():
    if 'file' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['file']

    if file.filename == '':
        return redirect(url_for('index'))
    
    if file and file.filename.lower().endswith(('png', 'jpg', 'jpeg')):
        # Save the uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join('static/uploads', filename)
        file.save(filepath)

        # Load and preprocess the image
        img = load_img(filepath, target_size=(224, 224))
        img = preprocess_image(img)

        # Make prediction
        prediction = model.predict(img)
        predicted_label = data_labels[np.argmax(prediction, axis=1)[0]]
        probability = np.max(prediction)  # Get the highest probability

        # Render the result page with all necessary information
        return render_template('result.html', 
                               pred=predicted_label, 
                               prob=f"{probability:.2f}",
                               image_url=url_for('static', filename='uploads/' + filename))
    
    return redirect(url_for('index'))




login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user_database.db'
Bootstrap(app)
db = SQLAlchemy(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Registration(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])



class LoginForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


from flask import flash

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if user.password == form.password.data:
                login_user(user)
                return redirect('/')
            else:
                form.password.errors.append('Incorrect password.')
        else:
            form.username.errors.append('Username does not exist.')

        flash('Invalid login details.', 'danger')

    return render_template('login.html', form=form)




from sqlalchemy.exc import IntegrityError

@app.route('/signup', methods=['GET', 'POST'])
def registration():
    form = Registration()
    if form.validate_on_submit():
        try:
            # Create and save the new user in the SQLAlchemy database
            new_user = User(username=form.username.data, email=form.email.data, password=form.password.data)
            db.session.add(new_user)
            db.session.commit()

            return redirect('/login')
        
        except IntegrityError as e:
            db.session.rollback()  # Rollback the session to clean up after the error
            form.email.errors.append('This email is already registered.')  # Add a specific error message for the email field
            print(f"IntegrityError during signup: {e}")

        except Exception as e:
            db.session.rollback()
            form.errors['database'] = [str(e)]
            print(f"Error during signup: {e}")

    return render_template('signup.html', form=form)



@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect('/login')



if __name__ == '__main__':
    app.run(debug=True)
