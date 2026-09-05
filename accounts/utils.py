# utils.py
from .models import Transaction, Account

def get_latest_account_data(user):
    """
    Fetch latest balance and last transaction date for each account of the user.
    Also calculates the total balance.
    """
    accounts = Account.objects.filter(user=user)
    account_data = []
    total_balance = 0

    for account in accounts:
        latest_transaction = Transaction.objects.filter(account=account).order_by("-date").first()
        latest_balance = latest_transaction.balance if latest_transaction else 0
        latest_transaction_date = latest_transaction.date if latest_transaction else None

        account_data.append({
            "account": account,
            "account_id": account.id,
            "latest_balance": latest_balance,
            "latest_transaction_date": latest_transaction_date,
        })

        total_balance += latest_balance

    return account_data, total_balance
