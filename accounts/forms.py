from django import forms
from .models import Account, Transaction
from django.forms.widgets import DateInput
from django.utils.timezone import now, timedelta
from datetime import date, timedelta



class UpdateBalanceForm(forms.Form):
    account = forms.ModelChoiceField(
        queryset=Account.objects.none(),  # ✅ Start with no accounts
        label="Select Account",
        empty_label="-- Select an Account --",  # ✅ Provide a default option
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    balance = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="New Balance",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    date = forms.DateField(
        initial=date.today,  # ✅ Default to today
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Transaction Date"
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # ✅ Extract user from kwargs
        super().__init__(*args, **kwargs)
        if user:
            self.fields['account'].queryset = Account.objects.filter(user=user)  # ✅ Load user's accounts

    def clean_date(self):
        selected_date = self.cleaned_data['date']
        today = now().date()
        max_allowed_date = today + timedelta(days=1)

        if selected_date > max_allowed_date:
            raise forms.ValidationError("You cannot select a date later than tomorrow.")

        return selected_date


# class UpdateBalanceForm(forms.Form):
#     account = forms.ModelChoiceField(
#         queryset=Account.objects.none(),  # ✅ Start with no accounts
#         label="Select Account",
#         empty_label="-- Select an Account --",  # ✅ Provide a default option
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     balance = forms.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         label="New Balance",
#         widget=forms.NumberInput(attrs={'class': 'form-control'})
#     )
#     date = forms.DateField(
#         widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#         label="Transaction Date"
#     )

#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user', None)  # ✅ Extract user from kwargs
#         super().__init__(*args, **kwargs)
#         if user:
#             self.fields['account'].queryset = Account.objects.filter(user=user)  # ✅ Load user's accounts

#     def clean_date(self):
#         selected_date = self.cleaned_data['date']
#         today = now().date()
#         tomorrow = today + timedelta(days=1)

#         if selected_date > tomorrow:
#             raise forms.ValidationError("You cannot select a date later than tomorrow.")

#         return selected_date


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name']



class TransactionForm(forms.ModelForm):
    date = forms.DateField(
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Date"
    )

    class Meta:
        model = Transaction
        fields = ['account', 'date', 'balance']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # ✅ Get user from view
        super().__init__(*args, **kwargs)
        if user:
            self.fields['account'].queryset = Account.objects.filter(user=user)  # ✅ Show only user's accounts






# class UpdateBalanceForm(forms.Form):
#     account = forms.ModelChoiceField(queryset=Account.objects.none(), label="Account")
#     balance = forms.DecimalField(max_digits=10, decimal_places=2, label="New Balance")

#     date = forms.DateField(
#         widget=DateInput(attrs={'type': 'date'}),
#         initial=date.today,  # ✅ Default to today
#     )

#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)
#         if user:
#             self.fields['account'].queryset = Account.objects.filter(user=user)

#     def clean_date(self):
#         selected_date = self.cleaned_data['date']
#         max_allowed_date = date.today() + timedelta(days=1)
#         if selected_date > max_allowed_date:
#             raise forms.ValidationError("You can't select a date later than tomorrow.")
#         return selected_date
