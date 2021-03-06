import re

from flask_wtf import FlaskForm
from wtforms.fields.html5 import EmailField, TelField
from wtforms.validators import DataRequired, Email, Regexp, ValidationError


class ContactDataForm(FlaskForm):
    email = EmailField(label='Adresy e-mail (oddzielone przecinkiem, np. a@a.pl, b@b.pl)',
                       validators=[
                           DataRequired(message='To pole nie może być puste.')
                       ])
    phone = TelField(label='Numery telefonu (oddzielone przecinkiem, np. 123123123, 234234234)',
                     validators=[
                         DataRequired(message='To pole nie może być puste.')
                     ])

    def validate_email(self, email):
        pattern = re.compile('^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$')

        for email_address in email.data.split(','):
            email_address = email_address.strip()

            if not pattern.match(email_address):
                raise ValidationError('Niepoprawne adresy e-mail.')

    def validate_phone(self, phones):
        pattern = re.compile('(?<!\w)(\(?(\+)?\d{2}\)?)?[ -]?\d{3}[ -]?((\d{3}[ -]?\d{3})|(\d{2}[ -]?\d{2}))(?!\w)')
        for phone_number in phones.data.split(','):
            phone_number = phone_number.strip()

            print(phone_number)

            if not pattern.match(phone_number):
                raise ValidationError('To pole nie zawiera poprawnych numerów telefonu.')
