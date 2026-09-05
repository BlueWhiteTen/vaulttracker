from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Account(models.Model):
    CURRENCY_CHOICES = [
        ('GBP', 'Pound (£)'),
        ('EUR', 'Euro (€)'),
        ('USD', 'Dollar ($)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ACCOUNT_TYPES = [
        ('savings', 'Savings'),
        ('investment', 'Investment'),
        ('property', 'Property'),
        ('pension', 'Pension'),
        ('debt', 'Debt / Mortgage'),
        ('asset', 'Asset'),
        ('other', 'Other'),
    ]
    name = models.CharField(max_length=255)
    icon = models.CharField(max_length=10, default='🏦')
    order = models.PositiveIntegerField(default=0)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='savings')
    target = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True, default='')
    latest_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='GBP')

    def __str__(self):
        return self.name


class Transaction(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    notes = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return f"{self.account.name} - {self.date} - {self.balance}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"
class UserProfile(models.Model):
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('el', 'Ελληνικά'),
    ]
    CURRENCY_CHOICES = [
        ('GBP', '£ GBP'),
        ('EUR', '€ EUR'),
        ('USD', '$ USD'),
    ]
    REMINDER_DAY_CHOICES = [(str(i), str(i)) for i in range(1, 29)] + [('last', 'Last day of month')]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(blank=True)
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='GBP')
    email_reminders = models.BooleanField(default=False)
    privacy_mode = models.BooleanField(default=False)
    show_icons = models.BooleanField(default=True)
    email_verified = models.BooleanField(default=False)
    reminder_day = models.CharField(max_length=4, choices=REMINDER_DAY_CHOICES, default='1')

    def __str__(self):
        return f"Profile of {self.user.username}"

class EmailVerificationToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token for {self.user.username}"
