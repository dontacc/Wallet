from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from .variables import *


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_balance = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username
    
    def deposit(self, amount):
        self.total_balance += amount
        self.save()


class Transaction(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, null=True)
    payment_status = models.SmallIntegerField(choices=PAYMENT_STATUS, default=0, verbose_name="ناموفق/موفق")
    title_status = models.SmallIntegerField(choices=TITLE_STATUS, verbose_name="برداشت/واریز",
                                            help_text="واریز به کیف پول یا برداشت از کیف پول", default=1)
    transaction_status = models.SmallIntegerField(choices=TRANSACTION_STATUS_CHOICES, default=0)
    amount = models.CharField(max_length=128)
    created = models.DateTimeField(auto_now_add=True)
    transaction_code = models.CharField(max_length=50, default='0')
    

    class Meta:
        db_table = "Transaction"


class Shaba(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete = models.CASCADE)
    shaba_number = models.CharField(max_length = 24, unique = True)
    bank_name = models.CharField(max_length=24)
    full_name = models.CharField(max_length=24)
    active_link = models.CharField(max_length=128, verbose_name="لینک ارسال شده", unique=True)
    # verified = models.BooleanField(default=False)
    created = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "shaba"
        verbose_name_plural = "shaba"

