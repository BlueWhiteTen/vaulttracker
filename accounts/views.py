import json
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Account, Transaction  # ✅ Import from models.py
from .forms import TransactionForm  # ✅ Import from forms.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django import forms
from accounts.models import Transaction, Account
from django.forms.widgets import DateInput
from decimal import Decimal
from collections import defaultdict
from .forms import UpdateBalanceForm
from django.contrib import messages
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout
from datetime import datetime
from .models import Notification, UserProfile
from django.utils import timezone
from django.utils.translation import activate
from .forms import AccountForm


import logging
logger = logging.getLogger(__name__)

class RegisterView(View):
    def get(self, request):
        form = UserCreationForm()
        return render(request, 'accounts/register.html', {'form': form})

    def post(self, request):
        form = UserCreationForm(request.POST)
        email = request.POST.get("email", "").strip()
        if form.is_valid():
            if not email:
                form.add_error(None, "Email is required.")
                return render(request, 'accounts/register.html', {'form': form})
            from django.contrib.auth.models import User as AuthUser
            if AuthUser.objects.filter(email=email).exists():
                form.add_error(None, "An account with this email already exists.")
                return render(request, 'accounts/register.html', {'form': form})
            user = form.save(commit=False)
            user.email = email
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.email = email
            profile.save()
            send_verification_email(request, user)
            messages.success(request, "Account created! Please check your email to verify your account.")
            return redirect("login")
        return render(request, 'accounts/register.html', {'form': form})  

class LoginView(View):
    def get(self, request):
        form = AuthenticationForm()
        return render(request, 'accounts/login.html', {'form': form})

    def post(self, request):
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            if not profile.email_verified:
                messages.error(request, "Please verify your email before logging in. Check your inbox.")
                return render(request, 'accounts/login.html', {'form': form, 'show_resend': True, 'unverified_user': user})
            login(request, user)
            remember_me = request.POST.get('remember_me')
            if remember_me:
                request.session.set_expiry(30 * 24 * 60 * 60)
            else:
                request.session.set_expiry(0)
            # Store last login in profile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            from django.utils import timezone as tz
            user.last_login = tz.now()
            user.save(update_fields=['last_login'])
            return redirect('myaccounts')

        return render(request, 'accounts/login.html', {'form': form})

def custom_logout(request):
    logout(request)
    return redirect("home")  # ✅ Redirect to the main page after logout


def home(request):
    if request.user.is_authenticated:
        return redirect('myaccounts')  # Redirect logged-in users to accounts list
    return render(request, 'accounts/home.html')  # Show home page for logged-out users


# class EditAccountsView(View):
#     def get(self, request):
#         user = request.user
#         accounts = Account.objects.filter(user=user)
#         form = AccountForm()

#         # ✅ Oldest transaction date
#         oldest_transaction = Transaction.objects.filter(account__in=accounts).order_by("date").first()
#         oldest_date = oldest_transaction.date if oldest_transaction else None  # If no transactions, None

#         # ✅ Fetch latest transactions for each account
#         account_data = []
#         for account in accounts:
#             latest_transaction = Transaction.objects.filter(account=account).order_by("-date").first()
#             latest_balance = latest_transaction.balance if latest_transaction else 0
#             latest_transaction_date = latest_transaction.date if latest_transaction else None

#             account_data.append({
#                 "account": account,
#                 "latest_balance": latest_balance,
#                 "latest_transaction_date": latest_transaction_date,
#             })

#         # ✅ Fetch the last 10 updates the user made
#         recent_updates = Transaction.objects.filter(account__in=accounts).order_by("-date")[:10]

#         return render(request, 'accounts/myaccounts.html', {
#             'accounts': accounts,
#             'account_data': account_data,
#             'recent_updates': recent_updates,
#             'form': form,
#             'oldest_date': oldest_date,  # ✅ Pass oldest date to template
#         })
#     def post(self, request):
#         form = AccountForm(request.POST)
#         if form.is_valid():
#             new_account = form.save(commit=False)
#             new_account.user = request.user  
#             new_account.save()
#             return redirect('edit_accounts')  

#         # ✅ If form is invalid, render page again with errors
#         user = request.user
#         accounts = Account.objects.filter(user=user)

#         oldest_transaction = Transaction.objects.filter(account__in=accounts).order_by("date").first()
#         oldest_date = oldest_transaction.date if oldest_transaction else None  

#         account_data = [
#             {
#                 "account": account,
#                 "latest_balance": (Transaction.objects.filter(account=account).order_by("-date").first() or {}).get("balance", 0),
#                 "latest_transaction_date": (Transaction.objects.filter(account=account).order_by("-date").first() or {}).get("date", None),
#             }
#             for account in accounts
#         ]

#         recent_updates = Transaction.objects.filter(account__in=accounts).order_by("-date")[:10]

#         return render(request, 'accounts/myaccounts.html', {
#             'accounts': accounts,
#             'account_data': account_data,
#             'recent_updates': recent_updates,
#             'form': form,  # ✅ Include form with errors
#             'oldest_date': oldest_date,
#         })


class EditAccountsView(View):
    def get(self, request):
        user = request.user
        accounts = Account.objects.filter(user=user)
        form = AccountForm()

        # Oldest transaction date
        oldest_transaction = Transaction.objects.filter(account__in=accounts).order_by("date").first()
        oldest_date = oldest_transaction.date if oldest_transaction else None  # If no transactions, None

        # Fetch latest transactions for each account
        account_data = []
        for account in accounts:
            latest_transaction = Transaction.objects.filter(account=account).order_by("-date").first()
            latest_balance = latest_transaction.balance if latest_transaction else 0
            latest_transaction_date = latest_transaction.date if latest_transaction else None

            account_data.append({
                "account": account,
                "latest_balance": latest_balance,
                "latest_transaction_date": latest_transaction_date,
                # "currency": account.currency,  # Include currency in account data
            })

        EMOJI_LIST = ['🏦','💰','📈','💵','💶','💷','🏠','🚗','✈️','🎓','💊','🛒','💎','🔐','📊','🌍','🏖️','👶','🐖','💳']
        from .models import UserProfile
        user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return render(request, 'accounts/editaccounts.html', {
            'accounts': accounts,
            'emoji_list': EMOJI_LIST,
            'show_icons': user_profile.show_icons,
            'account_data': account_data,
            'form': form,
            'oldest_date': oldest_date,  # Pass oldest date to template
        })

    def post(self, request):
        if request.POST.get('bulk_add'):
            names = request.POST.getlist('names[]')
            currencies = request.POST.getlist('currencies[]')
            types = request.POST.getlist('types[]')
            added = 0
            for i, (name, currency) in enumerate(zip(names, currencies)):
                name = name.strip()
                account_type = types[i] if i < len(types) else 'savings'
                if name:
                    Account.objects.create(
                        user=request.user,
                        name=name,
                        currency=currency or 'GBP',
                        account_type=account_type or 'savings'
                    )
                    added += 1
            if added:
                messages.success(request, f"{added} account(s) added successfully.")
            return redirect('edit_accounts')

        form = AccountForm(request.POST)
        if form.is_valid():
            new_account = form.save(commit=False)
            new_account.user = request.user
            new_account.currency = request.POST.get('currency', 'GBP')
            new_account.save()
            return redirect('edit_accounts')

        # If form is invalid, render page again with errors
        user = request.user
        accounts = Account.objects.filter(user=user)

        oldest_transaction = Transaction.objects.filter(account__in=accounts).order_by("date").first()
        oldest_date = oldest_transaction.date if oldest_transaction else None

        account_data = []
        for account in accounts:
            latest_transaction = Transaction.objects.filter(account=account).order_by("-date").first()
            account_data.append({
                "account": account,
                "latest_balance": latest_transaction.balance if latest_transaction else 0,
                "latest_transaction_date": latest_transaction.date if latest_transaction else None,
            })

        from .models import UserProfile
        user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return render(request, 'accounts/editaccounts.html', {
            'accounts': accounts,
            'emoji_list': EMOJI_LIST,
            'show_icons': user_profile.show_icons,
            'account_data': account_data,
            'form': form,  # Include form with errors
            'oldest_date': oldest_date,
        })

    
@method_decorator(login_required, name='dispatch')
class AddTransactionView(View):
    def get(self, request):
        form = TransactionForm(user=request.user)  # ✅ Pass user to form
        return render(request, 'accounts/add_transaction.html', {'form': form})

    def post(self, request):
        form = TransactionForm(request.POST, user=request.user)  # ✅ Pass user to form
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.account.user = request.user  # Ensure account belongs to the user
            transaction.save()
            return redirect('myaccounts')
        return render(request, 'accounts/add_transaction.html', {'form': form})


# def myaccounts(request):
#     user = request.user
#     accounts = Account.objects.filter(user=user).order_by("order", "id")

#     # ✅ Fetch latest transactions for each account
#     account_data = []
#     total_balance = 0  # ✅ Track total balance correctly

#     for account in accounts:
#         latest_transaction = Transaction.objects.filter(account=account).order_by("-date").first()

#         # ✅ Get latest balance from the latest transaction
#         latest_balance = latest_transaction.balance if latest_transaction else 0
#         latest_transaction_date = latest_transaction.date if latest_transaction else None

#         # ✅ Store account data (including ID for form URL)
#         account_data.append({
#             "account": account,
#             "account_id": account.id,  # ✅ Ensure template gets account.id
#             "latest_balance": latest_balance,
#             "latest_transaction_date": latest_transaction_date,
#         })

#         total_balance += latest_balance  # ✅ Add to total balance
#     if request.method == "POST":
#         form = UpdateBalanceForm(request.POST, user=user)  # ✅ Pass user to the form
#         if form.is_valid():
#             account = form.cleaned_data["account"]
#             new_balance = form.cleaned_data["balance"]
#             date = form.cleaned_data["date"]

#             # ✅ Save transaction
#             Transaction.objects.create(account=account, balance=new_balance, date=date)
#             account.latest_balance = new_balance  # ✅ Update account balance
#             account.save()

#             # ✅ Create notification
#             Notification.objects.create(
#                 user=request.user,
#                 message=f"Balance updated for {account.name}!",
#                 created_at=timezone.now()
#             )
#             messages.success(request, f"Balance updated for {account.name}!")
#             return redirect("myaccounts")

#     else:
#         form = UpdateBalanceForm(user=user)  # ✅ Pass user here too

    
#     # ✅ Prepare chart data
#     chart_data = defaultdict(list)
#     transactions = Transaction.objects.filter(account__user=user).order_by("date")
    
#     for transaction in transactions:
#         chart_data[transaction.account.name].append({
#             "date": transaction.date.strftime("%Y-%m-%d"),
#             "balance": float(transaction.balance),
#         })



# Cache exchange rates in memory to avoid repeated API calls
_rate_cache = {}
_rate_cache_time = {}

def get_exchange_rates(base_currency):
    """Fetch live exchange rates, cached for 1 hour."""
    import urllib.request
    import time

    now = time.time()
    if base_currency in _rate_cache and now - _rate_cache_time.get(base_currency, 0) < 3600:
        return _rate_cache[base_currency]

    try:
        url = f"https://open.er-api.com/v6/latest/{base_currency}"
        with urllib.request.urlopen(url, timeout=3) as response:
            data = json.loads(response.read())
            if data.get("result") == "success":
                rates = data.get("rates", {})
                _rate_cache[base_currency] = rates
                _rate_cache_time[base_currency] = now
                return rates
    except Exception:
        pass

    fallback = {
        "GBP": {"GBP": 1, "EUR": 1.17, "USD": 1.27},
        "EUR": {"GBP": 0.85, "EUR": 1, "USD": 1.08},
        "USD": {"GBP": 0.79, "EUR": 0.93, "USD": 1},
    }
    return fallback.get(base_currency, {"GBP": 1, "EUR": 1.17, "USD": 1.27})


def myaccounts(request):
    user = request.user
    accounts = Account.objects.filter(user=user)

    # Selected display currency from session (default GBP)
    display_currency = request.session.get("currency", "GBP")

    # Fetch live exchange rates based on display currency
    rates = get_exchange_rates(display_currency)

    CURRENCY_SYMBOLS = {"GBP": "£", "EUR": "€", "USD": "$"}
    display_symbol = CURRENCY_SYMBOLS.get(display_currency, "£")

    # Search filter
    search_query = request.GET.get('q', '').strip()

    # Inactivity threshold: 30 days
    from datetime import date as date_cls, timedelta as td
    inactivity_threshold = date_cls.today() - td(days=30)

    # Fetch latest transactions for each account
    account_data = []
    total_balance = 0
    total_assets = 0
    total_debts = 0

    for account in accounts:
        latest_transaction = Transaction.objects.filter(account=account).order_by("-date").first()
        latest_balance_native = latest_transaction.balance if latest_transaction else 0
        latest_transaction_date = latest_transaction.date if latest_transaction else None

        # Convert balance to display currency
        account_currency = getattr(account, "currency", "GBP") or "GBP"
        if account_currency == display_currency:
            converted_balance = float(latest_balance_native)
        else:
            # Convert: native -> display currency via rates
            # rates are: 1 display_currency = X other_currency
            # So to convert FROM account_currency TO display_currency:
            # we need rate of account_currency in terms of display_currency
            # Get rates based on account currency, then pick display currency
            account_rates = get_exchange_rates(account_currency)
            rate = account_rates.get(display_currency, 1)
            converted_balance = float(latest_balance_native) * rate

        # Inactivity check
        is_inactive = latest_transaction_date is not None and latest_transaction_date < inactivity_threshold
        is_inactive = is_inactive or latest_transaction_date is None

        account_data.append({
            "account": account,
            "account_id": account.id,
            "latest_balance_native": float(latest_balance_native),
            "latest_balance": round(converted_balance, 2),
            "latest_transaction_date": latest_transaction_date,
            "account_currency": account_currency,
            "account_symbol": CURRENCY_SYMBOLS.get(account_currency, "£"),
            "is_inactive": is_inactive,
        })

        if account.account_type == "debt":
            total_debts += converted_balance
        else:
            total_assets += converted_balance

    # Apply search filter
    if search_query:
        account_data = [d for d in account_data if search_query.lower() in d['account'].name.lower()]

    # Fetch the last 10 updates
    recent_updates = Transaction.objects.filter(account__in=accounts).order_by("-date")[:10]

    if request.method == "POST":
        form = UpdateBalanceForm(request.POST, user=user)
        if form.is_valid():
            account = form.cleaned_data["account"]
            new_balance = form.cleaned_data["balance"]
            date = form.cleaned_data["date"]

            Transaction.objects.create(account=account, balance=new_balance, date=date)
            account.latest_balance = new_balance
            account.save()

            Notification.objects.create(
                user=request.user,
                message=f"Balance updated for {account.name}!",
                created_at=timezone.now()
            )
            messages.success(request, f"Balance updated for {account.name}!")
            return redirect("myaccounts")
    else:
        form = UpdateBalanceForm(user=user)

    # Prepare chart data (in native currency per account)
    chart_data = defaultdict(list)
    transactions = Transaction.objects.filter(account__user=user).order_by("date")
    for transaction in transactions:
        chart_data[transaction.account.name].append({
            "date": transaction.date.strftime("%Y-%m-%d"),
            "balance": float(transaction.balance),
        })

    # Calculate net worth at different time periods
    from datetime import date as date_type, timedelta
    today = date_type.today()
    periods = {
        "30d": today - timedelta(days=30),
        "3m": today - timedelta(days=90),
        "6m": today - timedelta(days=180),
        "1y": today - timedelta(days=365),
    }

    def get_net_worth_at(target_date):
        total = 0
        for account in accounts:
            tx = Transaction.objects.filter(
                account=account,
                date__lte=target_date
            ).order_by("-date").first()
            if tx:
                acc_currency = getattr(account, "currency", "GBP") or "GBP"
                if acc_currency == display_currency:
                    bal = float(tx.balance)
                else:
                    acc_rates = get_exchange_rates(acc_currency)
                    rate = acc_rates.get(display_currency, 1)
                    bal = float(tx.balance) * rate
                if account.account_type == "debt":
                    total -= bal
                else:
                    total += bal
        return round(total, 2)

    current_net_worth = round(total_assets - total_debts, 2)

    period_comparison = []
    for label, past_date in [("30 days", periods["30d"]), ("3 months", periods["3m"]), ("6 months", periods["6m"]), ("1 year", periods["1y"])]:
        past_worth = get_net_worth_at(past_date)
        if past_worth != 0:
            change = current_net_worth - past_worth
            pct = (change / abs(past_worth)) * 100
        else:
            change = current_net_worth
            pct = 0
        period_comparison.append({
            "label": label,
            "past_worth": past_worth,
            "change": round(change, 2),
            "pct": round(pct, 1),
        })

    return render(request, "accounts/myaccounts.html", {
        "account_data": account_data,
        "total_balance": round(total_balance, 2),
        "display_currency": display_currency,
        "display_symbol": display_symbol,
        "chart_data_json": json.dumps(chart_data),
        "dot_colors": ["hsl({},55%,42%)".format(i * 137 % 360) for i in range(len(account_data))],
        "form": form,
        "recent_updates": recent_updates,
        "privacy_mode": UserProfile.objects.get_or_create(user=user)[0].privacy_mode,
        "show_icons": UserProfile.objects.get_or_create(user=user)[0].show_icons,
        "total_assets": round(total_assets, 2),
        "total_debts": round(total_debts, 2),
        "net_worth": round(total_assets - total_debts, 2),
        "total_balance": round(total_assets - total_debts, 2),
        "period_comparison": period_comparison,
        "search_query": search_query,
    })

class TransactionForm(forms.ModelForm):
    date = forms.DateField(
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],   # Ensure DD/MM/YYYY format
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'})  # Show calendar picker
    )

    class Meta:
        model = Transaction
        fields = ['account', 'date', 'balance']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Get user from the view
        super().__init__(*args, **kwargs)
        if user:
            self.fields['account'].queryset = Account.objects.filter(user=user)  # ✅ Show only user's accounts

class AccountForm(forms.ModelForm):
    CURRENCY_CHOICES = [
        ('GBP', '£ GBP'),
        ('EUR', '€ EUR'),
        ('USD', '$ USD'),
    ]
    currency = forms.ChoiceField(choices=CURRENCY_CHOICES, initial='GBP')

    class Meta:
        model = Account
        fields = ['name', 'currency']


@login_required
def update_account_currency(request, account_id):
    if request.method == "POST":
        account = get_object_or_404(Account, id=account_id, user=request.user)
        currency = request.POST.get("currency", "GBP")
        if currency in ["GBP", "EUR", "USD"]:
            account.currency = currency
            account.save()
            messages.success(request, f"Currency updated for {account.name}.")
    # Go back to wherever we came from
    referer = request.META.get("HTTP_REFERER", "")
    if "edit" in referer:
        return redirect("edit_accounts")
    elif "account" in referer:
        return redirect("account_detail", account_id=account_id)
    return redirect("myaccounts")


@login_required
@csrf_exempt  # Allows AJAX requests
def reset_account(request, account_id):
    if request.method == "POST":
        try:
            account = Account.objects.get(id=account_id, user=request.user)

            # ✅ Delete all transactions for this account
            Transaction.objects.filter(account=account).delete()

            # ✅ Reset the balance to £0
            account.latest_balance = 0
            account.save()

            return JsonResponse({"success": True})
        except Account.DoesNotExist:
            return JsonResponse({"success": False, "error": "Account not found."})
    
    return JsonResponse({"success": False, "error": "Invalid request."})

@login_required
def delete_account(request, account_id):
    if request.method == "POST":
        account = get_object_or_404(Account, id=account_id, user=request.user)
        account.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)



def custom_logout(request):
    logout(request)
    return redirect("home")  # ✅ Redirect to the main page after logout


def home(request):
    if request.user.is_authenticated:
        return redirect('myaccounts')  # Redirect logged-in users to accounts list
    return render(request, 'accounts/home.html')  # Show home page for logged-out users


  
def example_view(request):
    Notification.objects.create(
        message="Account updated",
        created_at=timezone.now()
    )
    return redirect('myaccounts')

def get_notifications_for_user(user):
    return Notification.objects.filter(user=user, is_read=False)

from django.shortcuts import redirect
from django.http import HttpResponseRedirect

def set_currency(request):
    if request.method == "POST":
        currency = request.POST.get("currency")
        if currency in ["GBP", "EUR", "USD"]:
            request.session["currency"] = currency  # Store the selection in session
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@csrf_exempt  # Allows AJAX calls
def set_language(request):
    if request.method == "POST":
        language = request.POST.get("language")
        if language in ["en", "el"]:  # Supported languages
            request.session["django_language"] = language
            activate(language)
            return JsonResponse({"success": True})
        return JsonResponse({"success": False, "error": "Invalid language"})
    
    return JsonResponse({"success": False, "error": "Invalid request"})
@login_required
def account_detail(request, account_id):
    account = get_object_or_404(Account, id=account_id, user=request.user)
    display_currency = request.session.get("currency", "GBP")
    CURRENCY_SYMBOLS = {"GBP": "£", "EUR": "€", "USD": "$"}
    display_symbol = CURRENCY_SYMBOLS.get(display_currency, "£")
    account_symbol = CURRENCY_SYMBOLS.get(account.currency, "£")
    sort_by = request.GET.get("sort", "date")
    sort_dir = request.GET.get("dir", "desc")
    order = "-" + sort_by if sort_dir == "desc" else sort_by
    transactions = Transaction.objects.filter(account=account).order_by(order)
    chart_data = [
        {"date": t.date.strftime("%Y-%m-%d"), "balance": float(t.balance)}
        for t in Transaction.objects.filter(account=account).order_by("date")
    ]
    if request.method == "POST":
        dates = request.POST.getlist("dates[]")
        balances = request.POST.getlist("balances[]")
        notes_list = request.POST.getlist("notes[]")
        added = 0
        for i, (date_str, balance_str) in enumerate(zip(dates, balances)):
            date_str = date_str.strip()
            balance_str = balance_str.strip()
            note = notes_list[i].strip() if i < len(notes_list) else ""
            if date_str and balance_str:
                try:
                    d = None
                    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
                        try:
                            d = datetime.strptime(date_str, fmt).date()
                            break
                        except ValueError:
                            continue
                    if not d:
                        errors.append(f"Row {row_num}: unrecognised date: {date_str}")
                        continue
                    b = float(balance_str)
                    Transaction.objects.create(account=account, balance=b, date=d, notes=note)
                    account.latest_balance = b
                    account.save()
                    added += 1
                except Exception:
                    pass
        if added:
            messages.success(request, f"{added} transaction(s) added.")
        return redirect("account_detail", account_id=account_id)
    # Current and first balance for percentage change
    all_by_date = Transaction.objects.filter(account=account).order_by("date")
    all_by_date_desc = Transaction.objects.filter(account=account).order_by("-date")
    first_tx = all_by_date.first()
    latest_tx = all_by_date_desc.first()
    current_balance = float(latest_tx.balance) if latest_tx else 0
    first_balance = float(first_tx.balance) if first_tx else 0
    if first_balance and first_balance != 0:
        pct_change = ((current_balance - first_balance) / abs(first_balance)) * 100
    else:
        pct_change = None

    return render(request, "accounts/account_detail.html", {
        "account": account,
        "transactions": transactions,
        "chart_data_json": json.dumps(chart_data),
        "sort_by": sort_by,
        "sort_dir": sort_dir,
        "display_symbol": display_symbol,
        "account_symbol": account_symbol,
        "transaction_count": transactions.count(),
        "current_balance": current_balance,
        "first_balance": first_balance,
        "pct_change": pct_change,
    })

@login_required
@csrf_exempt
def delete_transaction(request, tx_id):
    if request.method == "POST":
        tx = get_object_or_404(Transaction, id=tx_id, account__user=request.user)
        tx.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})

@login_required
def profile(request):
    from .models import UserProfile
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_profile":
            email = request.POST.get("email", "").strip()
            language = request.POST.get("language", "en")
            currency = request.POST.get("currency", "GBP")
            email_reminders = request.POST.get("email_reminders") == "on"
            privacy_mode = request.POST.get("privacy_mode") == "on"
            profile.privacy_mode = privacy_mode
            profile.show_icons = request.POST.get("show_icons") == "on"
            reminder_day = request.POST.get("reminder_day", "1")

            profile.email = email
            profile.language = language
            profile.currency = currency
            profile.email_reminders = email_reminders
            profile.reminder_day = reminder_day
            profile.save()

            # Apply language and currency to session
            request.session["currency"] = currency
            from django.utils.translation import activate
            activate(language)
            request.session["_language"] = language

            messages.success(request, "Profile updated successfully.")

        elif action == "change_username":
            new_username = request.POST.get("username", "").strip()
            if new_username and new_username != request.user.username:
                from django.contrib.auth.models import User as AuthUser
                if AuthUser.objects.filter(username=new_username).exists():
                    messages.error(request, "That username is already taken.")
                else:
                    request.user.username = new_username
                    request.user.save()
                    messages.success(request, "Username updated successfully.")

        elif action == "change_password":
            current = request.POST.get("current_password")
            new_pass = request.POST.get("new_password")
            confirm = request.POST.get("confirm_password")

            if not request.user.check_password(current):
                messages.error(request, "Current password is incorrect.")
            elif new_pass != confirm:
                messages.error(request, "New passwords do not match.")
            elif len(new_pass) < 8:
                messages.error(request, "Password must be at least 8 characters.")
            else:
                request.user.set_password(new_pass)
                request.user.save()
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, request.user)
                messages.success(request, "Password updated successfully.")

        return redirect("profile")

    return render(request, "accounts/profile.html", {
        "profile": profile,
        "reminder_days": [str(i) for i in range(1, 29)] + ["last"],
    })

@login_required
def export_csv(request):
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="savings_export.csv"'
    response.write('﻿')  # BOM for Excel UTF-8 compatibility

    writer = csv.writer(response)
    writer.writerow(['Account', 'Currency', 'Balance', 'Date'])

    accounts = Account.objects.filter(user=request.user)
    for account in accounts:
        transactions = Transaction.objects.filter(account=account).order_by('date')
        for tx in transactions:
            writer.writerow([
                account.name,
                account.currency,
                tx.balance,
                tx.date.strftime('%Y-%m-%d'),
            ])

    return response

@login_required
def import_csv(request):
    import csv
    import io

    if request.method == "POST" and request.FILES.get("csv_file"):
        csv_file = request.FILES["csv_file"]
        decoded = csv_file.read().decode("utf-8-sig").replace('﻿', '')
        # Clean up the rows by stripping BOM from field names
        reader = csv.DictReader(io.StringIO(decoded))

        imported = 0
        errors = []

        for row_num, row in enumerate(reader, start=2):
            try:
                account_name = row.get("Account", "").strip().lstrip("\ufeff").strip()
                currency = row.get("Currency", "GBP").strip()
                balance = float(row.get("Balance", 0))
                date_str = row.get("Date", "").strip()

                if not account_name or not date_str:
                    continue

                from datetime import datetime
                date = None
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
                    try:
                        date = datetime.strptime(date_str, fmt).date()
                        break
                    except ValueError:
                        continue
                if not date:
                    errors.append(f"Row {row_num}: unrecognised date: {date_str}")
                    continue

                account, created = Account.objects.get_or_create(
                    user=request.user,
                    name=account_name,
                    defaults={"currency": currency}
                )

                Transaction.objects.create(
                    account=account,
                    balance=balance,
                    date=date
                )
                account.latest_balance = balance
                account.save()
                imported += 1

            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")

        if imported:
            messages.success(request, f"{imported} transaction(s) imported successfully.")
        if errors:
            for error in errors[:5]:
                messages.error(request, error)

        return redirect("myaccounts")

    return render(request, "accounts/import_csv.html")

@login_required
def rename_account(request, account_id):
    if request.method == "POST":
        account = get_object_or_404(Account, id=account_id, user=request.user)
        name = request.POST.get("name", "").strip()
        icon = request.POST.get("icon", "").strip()
        account_type = request.POST.get("account_type", "").strip()
        target = request.POST.get("target", "").strip()
        notes = request.POST.get("account_notes", None)
        if name:
            account.name = name
        if icon:
            account.icon = icon
        if account_type:
            account.account_type = account_type
        if target:
            try:
                account.target = float(target)
            except ValueError:
                pass
        elif "target" in request.POST and target == "":
            account.target = None
        if notes is not None:
            account.notes = notes
        if name or icon or account_type or "target" in request.POST or notes is not None:
            account.save()
            messages.success(request, "Account updated.")
    return redirect("edit_accounts")

@login_required
def reorder_accounts(request):
    if request.method == "POST":
        import json
        data = json.loads(request.body)
        order = data.get("order", [])
        for i, account_id in enumerate(order):
            Account.objects.filter(id=account_id, user=request.user).update(order=i)
        return JsonResponse({"success": True})
    return JsonResponse({"success": False})

import secrets
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site

def send_verification_email(request, user):
    from .models import EmailVerificationToken
    token = secrets.token_urlsafe(32)
    EmailVerificationToken.objects.update_or_create(
        user=user,
        defaults={"token": token}
    )
    domain = request.get_host()
    link = f"https://{domain}/verify-email/{token}/"
    send_mail(
        subject="Verify your Vault email",
        message=f"Hi {user.username},\n\nClick the link below to verify your email:\n\n{link}\n\nIf you didn't register, ignore this email.",
        from_email="Vault <vaulttrackeronline@gmail.com>",
        recipient_list=[user.email],
        fail_silently=False,
    )

def verify_email(request, token):
    from .models import EmailVerificationToken
    try:
        verification = EmailVerificationToken.objects.get(token=token)
        profile, _ = UserProfile.objects.get_or_create(user=verification.user)
        profile.email_verified = True
        profile.save()
        verification.delete()
        messages.success(request, "Email verified! You can now log in.")
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, "Invalid or expired verification link.")
    return redirect("login")

def resend_verification(request):
    if request.user.is_authenticated:
        send_verification_email(request, request.user)
        messages.success(request, "Verification email sent!")
        return redirect("profile")
    return redirect("login")
