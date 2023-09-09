import logging
# from azbankintro import iban_validate, IBANValidationException
from django.core.validators import RegexValidator
from rest_framework import serializers
from persiantools.jdatetime import *
from .models import *
from .variables import *
from django.utils import timezone
from datetime import datetime

shaba_regex = RegexValidator(regex = r'^\d{24}$', message = "must be 24 digits")






class TransactionSerializer(serializers.ModelSerializer):
    #orderId = serializers.SerializerMethodField(method_name='order_id', allow_null = True)
    time = serializers.SerializerMethodField(initial=timezone.now, source='created', method_name='convert_time')
    amount = serializers.IntegerField(required=True)
    status = serializers.IntegerField(source='transaction_status', required=False)
    msg = serializers.SerializerMethodField(method_name="show_status_msg")
    
    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'status', 'time', 'msg']

    def show_status_msg(self, obj):
        return TRANSACTION_STATUS_CHOICES[obj.transaction_status][1]

    def show_status(self, obj):
        return TRANSACTION_STATUS_CHOICES[obj.transaction_status][0]


    def convert_time(self, obj):
        date = JalaliDate(obj.created)
        date_time = str(JalaliDateTime(obj.created))
        time = date_time[11:16]
        date = date_time.replace('-', '/')[: 11]
        
        result = f"{time} | {date}"
        return result


class ActiveLinkSerializer(serializers.Serializer):
    activeLink = serializers.CharField(required=True, 
                                       max_length=72, 
                                       help_text=("string") )
    



class ShabaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Shaba
        fields = '__all__'


    def to_representation(self, instance):
        data = {
            'iban': instance.shaba_number,
            'name': instance.full_name,
            'bank': instance.bank_name,
            'updatedAt': str(JalaliDate(instance.created)).replace('-', '/')
        }

        return data


class ShabaPostSerializer(serializers.Serializer):
    iban = serializers.CharField(required = True, max_length = 128, 
                                 validators = [shaba_regex], 
                                 help_text = ("string"))
    bank = serializers.CharField(required = True, help_text = ("string") )
    name = serializers.CharField(required = True, help_text = ("string") )
    
    # def validate_iban(self, obj):
    #     if obj.isdigit() == False:
    #         raise serializers.ValidationError("شماره نامعتبر")
    #     # elif models.Shaba.objects.filter(wallet_id=self.context["request"].user.wallet.id,
    #     #                                  shaba_number__iexact=obj, verified=True).exists():
    #     #     raise serializers.ValidationError("شماره شبا قبلا ثبت شده است.")

    #     try:
    #         iban_validate('IR' + obj)
    #         logging.debug('شماره IBAN معتبر است.')

    #         return obj
    #     except IBANValidationException:
    #         logging.debug('شماره IBAN نا معتبر است')
    #         raise serializers.ValidationError("شماره شبا نامعتبر است.")
        
    


class ShabaDataSerializer(serializers.ModelSerializer):
    fullName = serializers.CharField(source="full_name")
    bank = serializers.CharField(source="bank_name")
    iban = serializers.CharField(source="shaba_number")


    class Meta:
        model = Shaba
        fields = ['fullName', 'bank', 'iban']

