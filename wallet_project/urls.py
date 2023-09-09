from django.urls import path
from .views import *

app_name= "wallets"

urlpatterns = [
    path("", WalletView.as_view(), name="wallet-page"), # wallet
    path("business-transaction/", BusinessTransactionHistory.as_view(), name="business-transaction"),
    path("personal-transaction/", PersonalTransactionHistory.as_view(), name="personal-transaction"),
    path("deposits/", Deposit.as_view(), name="deposit-page"),
    path("payment-callback/" , PaymentCallBack.as_view() , name="payment-callback"), # callback
    path("wallet-callback/", WalletCallBack.as_view(), name="wallet-callback"),
    path("shaba-registration/", ShabaRegistration.as_view(), name="shaba-registration"),
    path("link-verification/<activeLink>", LinkVerification.as_view(), name="link-verification"),
    path("send-link-again/", SendLinkAgain.as_view(), name="send-link-again"),
    path("transaction-check/<tc>/", TransactionCheck.as_view(), name="transaction checker"),
    path("checkout/", ImmediateCheckout.as_view(), name="immediate-checkout"),
    path("shaba-data/<activeLink>", ShabaData.as_view(), name="shaba-date"),
    path("loading-page/", LoadingPage.as_view(), name="s_page"),
    path("shaba-cancel/", ShabaCancel.as_view(), name="shaba-cancel")

]