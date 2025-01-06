from flask import Blueprint, render_template, redirect, url_for, request, flash
import shelve
from .Forms import Feedback, Addfaq
from .faq import Faq
from flask_login import current_user

views = Blueprint('views', __name__)


@views.context_processor
def inject_user():
    return dict(user=current_user)

@views.route('/')
def home():
    return render_template('home.html')


@views.route('/contactUs', methods=['GET', 'POST'])
def contact_us():
    form = Feedback(request.form)
    if request.method == 'POST' and form.validate():
        flash('Thanks for your feedback!', category='success')
        return redirect(url_for('views.home'))
    return render_template('contactUs.html', form=form)


@views.route('/faq')
def faq():
    db = shelve.open('faq.db', 'c')
    try:
        faq_entries = db.get('Faqs', {})

    except KeyError:
        print("Error in retrieving Products from products.db.")
        faq_entries = {}

    db.close()
    faqs = []
    for key in faq_entries:
        faq = faq_entries.get(key)
        faqs.append(faq)

    return render_template('faq.html', faqs=faqs)


@views.route('/faqDB')
def faqDB():
    db = shelve.open('faq.db', 'c')
    try:
        faq_entries = db.get('Faqs', {})

    except KeyError:
        print("Error in retrieving Products from products.db.")
        faq_entries = {}

    db.close()
    faqs = []
    for key in faq_entries:
        faq = faq_entries.get(key)
        faqs.append(faq)

    return render_template('faqDB.html', faqs=faqs)


@views.route('/add-faq', methods=['GET', 'POST'])
def add_faq():
    form = Addfaq(request.form)
    if request.method == 'POST' and form.validate():
        db = shelve.open('faq.db')

        try:
            faq_dict = db['Faqs']
        except:
            print("Error in retrieving Users from faq.db.")
            faq_dict = {}

        Faq.count_id = len(faq_dict)

        faq = Faq(form.question.data,
                  form.answer.data)

        faq_dict[Faq.count_id] = faq

        db['Faqs'] = faq_dict

        db.close()
        return redirect(url_for('views.faq'))
    return render_template('addfaq.html', form=form)


@views.route('/updateFAQ/<int:id>/', methods=['GET', 'POST'])
def update_faq(id):
    form = Addfaq(request.form)
    if request.method == 'POST' and form.validate():
        db = shelve.open('faq.db', 'w')
        faq_dict = db['Faqs']

        faq = faq_dict.get(id)
        faq.set_question(form.question.data)
        faq.set_answer(form.answer.data)

        db['Faqs'] = faq_dict
        db.close()

        return redirect(url_for('views.faqDB'))
    else:
        db = shelve.open('faq.db', 'r')
        faq_dict = db['Faqs']
        db.close()

        faq = faq_dict.get(id)
        form.question.data = faq.get_question()
        form.answer.data = faq.get_answer()

        return render_template('updatefaq.html', form=form)


@views.route('/deleteFAQ/<int:id>', methods=['POST'])
def delete_faq(id):
    db = shelve.open('faq.db', 'w')
    faq_dict = db['Faqs']

    faq_dict.pop(id)

    db['Users'] = faq_dict
    print(f"Number of unique keys in the dictionary after: {len(faq_dict)}")

    db.close()

    return redirect(url_for('auth.faqDB'))
