from itertools import groupby
from os import listdir
from os.path import isfile, join

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort

# database
from app import app
from app.forms.ContactForms import ContactForm, MerchContactForm
from app.models.GalleryModel import Gallery
from app.models.MailModel import Mail
from app.resources.AlbumsResource import get_all_albums
from app.resources.ConcertsResource import get_planned_concerts, get_past_concerts
from app.resources.ContactDataResource import get_contact_item_by_key
from app.resources.GalleriesResource import get_all_galleries, get_gallery_by_secure_title
from app.resources.MerchResource import get_all_merch, get_item_from_merch
from app.resources.SizeTablesResource import get_table_by_key
from app.resources.SlidesResource import get_slides_for_display
from app.resources.TextsResource import get_text_by_page

MainSite = Blueprint('MainSite', __name__)


@MainSite.context_processor  # inject footer form to all templates
def inject_variables():
    form = ContactForm()

    cached_form = session.get('contact_form_data', {})

    if cached_form:
        errors = cached_form.get('errors')

        form.email.data = cached_form.get('email')
        form.email.errors = errors.get('email')

        form.topic.data = cached_form.get('topic')
        form.topic.errors = errors.get('topic')

        form.message.data = cached_form.get('message')
        form.message.errors = errors.get('message')

        session.pop('contact_form_data')

    return dict(
        form=form
    )


@MainSite.route('/')
def index():
    closest_concerts = get_planned_concerts(3)
    slides = get_slides_for_display()

    return render_template('index.html',
                           closest_concerts=closest_concerts,
                           slides=slides
                           )


@MainSite.route('/onas/czzk')
def about_czzk():
    page = 'czzk'
    chapters = get_text_by_page(page)

    return render_template('about-czzk.html',
                           chapters=chapters
                           )


@MainSite.route('/onas/muzyka')
def about_music():
    page = 'muzyka'
    chapters = get_text_by_page(page)
    albums = get_all_albums()
    if albums:
        albums = groupby(albums, lambda x: x.year)

    # for key, group in groupby(albums, lambda x: x.year):
    #     print(key)
    #     for album in group:
    #         print(album.title)
    # https://stackoverflow.com/questions/45732065/group-list-by-some-value-in-python
    # https://stackoverflow.com/questions/773/how-do-i-use-pythons-itertools-groupby
    # the other idea: make a dict ({year=[album1, album2]})

    return render_template('about-music.html',
                           chapters=chapters,
                           albums=albums
                           )


@MainSite.route('/onas/kazik')
def about_kazik():
    return render_template('about-kazik.html')


@MainSite.route('/koncerty')
def concerts():
    planned_concerts = get_planned_concerts()
    past_concerts = get_past_concerts()

    return render_template('concerts.html',
                           planned_concerts=planned_concerts,
                           past_concerts=past_concerts
                           )


@MainSite.route('/multimedia/audio')
def multimedia_audio():
    return render_template('multimedia-audio.html')


@MainSite.route('/multimedia/galeria')
def multimedia_galleries():
    page = request.args.get('strona', 1, type=int)

    galleries = get_all_galleries(page)

    return render_template('multimedia-galleries.html',
                           galleries=galleries
                           )


@MainSite.route('/multimedia/galeria/<string:gallery_secure_title>')
def multimedia_specific_gallery(gallery_secure_title):
    if not gallery_secure_title:
        abort(404)
    # page = request.args.get('strona', 1, type=int)

    gallery = Gallery(get_gallery_by_secure_title(gallery_secure_title))

    try:
        # paginated_photos = gallery.paginate_photos(page=page)
        paginated_photos = gallery.get_photos()
        videos = gallery.get_videos()
    except FileNotFoundError:
        return render_template('multimedia-specific-gallery.html',
                               gallery=gallery,
                               paginated_photos=[],
                               videos=[])

    return render_template('multimedia-specific-gallery.html',
                           gallery=gallery,
                           paginated_photos=paginated_photos,
                           videos=videos
                           )


@MainSite.route('/multimedia/gadzety')
def multimedia_merch():
    items = get_all_merch()

    return render_template('multimedia-merch.html',
                           items=items
                           )


@MainSite.route('/multimedia/gadzety/<string:merch_item>')
def multimedia_merch_item(merch_item):
    item = get_item_from_merch(merch_item)
    merch_form = MerchContactForm()

    cached_form = session.get('merch_form_data', {})

    if cached_form:
        errors = cached_form.get('errors')

        merch_form.email.data = cached_form.get('email')
        merch_form.email.errors = errors.get('email')

        merch_form.message.data = cached_form.get('message')
        merch_form.message.errors = errors.get('message')

        session.pop('merch_form_data')

    size_table = get_table_by_key(item.size_table)

    return render_template('multimedia-merch-item.html',
                           size_table=size_table,
                           item=item,
                           merch_form=merch_form
                           )


@MainSite.route('/multimedia/archiwum')
def multimedia_archive():
    return render_template('multimedia-archive.html')


@MainSite.route('/kontakt')
def contact():
    rider_dir = app.config['UPLOAD_FOLDER'] + '/files/rider/current'
    rider_files = [f for f in listdir(rider_dir) if isfile(join(rider_dir, f))]
    rider_files.sort(reverse=True)

    if rider_files:
        rider = rider_files[0]
    else:
        rider = ''

    raw_phone_numbers = get_contact_item_by_key('phone')
    raw_emails = get_contact_item_by_key('email')

    phone_numbers = []
    emails = []

    for email_address in raw_emails.value.split(','):
        emails.append(email_address.strip())

    for email_address in raw_phone_numbers.value.split(','):
        phone_numbers.append(email_address.strip())

    return render_template('contact.html', rider=rider, phone_numbers=phone_numbers, emails=emails)


@MainSite.route('/send-message', methods=['POST', 'GET'])
def send_message():
    if request.args.get('type') == 'merch':
        form_type = 'merch'
        form = MerchContactForm()
    else:
        form_type = 'contact'
        form = ContactForm()

    # Get data
    email = request.form.get('email')
    topic = request.form.get('topic')
    message = request.form.get('message')

    form.email.data = email
    form.message.data = message
    if form_type == 'contact':
        form.topic.data = topic

    if request.method == 'POST' and form.validate_on_submit():
        if form_type == 'merch':
            settings = {
                'type': form_type,
                'item': request.args.get('merch_item')
            }
        else:
            settings = {
                'type': form_type,
                'item': None
            }
        # send email
        mail = Mail(topic=topic, content=message, reply_email=email, settings=settings)

        mail.send()

        flash('Twoja wiadomość została wysłana.', 'message-success')

    elif request.method == 'POST' and not form.validate_on_submit():
        print(form.errors)
        if form_type == 'contact':
            session['contact_form_data'] = {
                'email': email,
                'topic': topic,
                'message': message,
                'errors': form.errors
            }
        else:
            session['merch_form_data'] = {
                'email': email,
                'message': message,
                'errors': form.errors
            }

        flash('Przepraszamy, wystąpił błąd podczas wysyłania wiadomości. Sprawdź swój formularz.', 'message-error')

    # Redirect to previous page
    page = request.args.get('page')

    if request.args.get('gallery'):
        gallery = request.args.get('gallery')

        return redirect(url_for(page, gallery_secure_title=gallery))
    elif request.args.get('merch_item'):
        merch_item = request.args.get('merch_item')

        return redirect(url_for(page, merch_item=merch_item))

    try:
        return redirect(url_for(page))
    except TypeError:
        return redirect(url_for('MainSite.index'))


@MainSite.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', form=ContactForm()), 404


@MainSite.errorhandler(500)
def internal_error(error):
    return render_template('500.html', form=ContactForm()), 500
