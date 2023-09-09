import logging
from accounts.variables import API
from .variables import *
from django.core.cache import cache
from django.shortcuts import redirect, reverse
from django.utils.crypto import get_random_string
from kavenegar import *
from rest_framework.throttling import UserRateThrottle
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import *
from .serializers import *
from persiantools.jdatetime import JalaliDate
from accounts import models as account_models
from django.http import HttpResponseRedirect
from orders.models import *
import requests
from unidecode import unidecode
from rest_framework.generics import ListAPIView, GenericAPIView
from .utils import *
from rest_framework_simplejwt.tokens import RefreshToken


#from wallets import 
from django.shortcuts import redirect





def redirect_view(request):
    #response = redirect('/redirect-success/')
    response = redirect('http://www.app.dosma.ir')
    # Set 'Test' header and then delete
    response['Content-Type'] = 'application/json'
    del response['Test']
    # Set 'Test Header' header
    response['Header'] = 'Test Header'
    return response
    # return redirect("https://app.dosma.ir/",)


def response_func(status: bool, msg: str, data: dict):
    res = {
        'status': status,
        'message': msg,
        'data': data
    }
    return res




class WalletView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        try:
            wallet = Wallet.objects.get(user_id=request.user.id)
            block_money = account_models.ExpertSkill.objects.filter(user_id=request.user.id).values('block_money').order_by('-block_money').first()


            if block_money == None:
                available_balance = wallet.total_balance
            else:
                available_balance = wallet.total_balance - block_money['block_money']
            

            data = {
                'id': wallet.id,
                'balance': (wallet.total_balance)/10,
                'availableBalance': available_balance/10,
            }
                
            return Response(response_func(True, 
                                          'wallet of user', 
                                          data
                                          ), status=status.HTTP_200_OK
                                          )
        
        except Exception as e:
            return Response(response_func(
                False,
                "",
                {"error": str(e)}
            ), status=status.HTTP_200_OK
            )



class BusinessTransactionHistory(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        history = Transaction.objects.filter(wallet_id=request.user.wallet.id,
                                            payment_status=1,
                                            transaction_status__in=[2, 3, 4, 5]).select_related('wallet').order_by('-created')
        serializer = TransactionSerializer(history, many=True, context={'request': request})
        if history.exists():
            
            return Response(response_func(
                True,
                'گردش حساب کاری',
                serializer.data
            ), status=status.HTTP_200_OK
            )
        

        return Response(response_func(
            True,
            "گردش حساب کاری خالی است",
            {}
        ), status=status.HTTP_200_OK
        )
        
        


        
        
class PersonalTransactionHistory(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            history = Transaction.objects.filter(wallet_id=request.user.wallet.id,
                                                payment_status__in=[0, 1],
                                                transaction_status__in=[0, 1]).select_related('wallet').order_by('-created')
            serializer = TransactionSerializer(history, many=True, context={'request': request})
            if history.exists():
                return Response(response_func(
                                True,
                                "گردش حساب شخصی",
                                serializer.data
                                ), status=status.HTTP_200_OK
                        )
        except Exception as e:
            return Response(response_func(
                                True,
                                "گردش حساب شخصی خالی است",
                                {}
                            ), status=status.HTTP_200_OK
                        )



class TransactionCheck(APIView):
    def get(self, request, tc):
        transaction_obj = Transaction.objects.get(transaction_code = tc)

        data = {
            "msg": transaction_obj.payment_status,
            "amount": transaction_obj.amount,
            "transactionStatus": transaction_obj.transaction_status
        }

        if transaction_obj.payment_status:
            return Response(response_func(True,
                                          "از طریق کارت بانکی شما پرداخت شده است.",
                                          data
                                          ), status=status.HTTP_200_OK
                            )
        return Response(response_func(
                            False,
                            "در صورت برداشت وجه ظرف مدت ۴۸ ساعت وجه برداشته‌ شده به حساب شما باز خواهد گشت.",
                            data
                        ), status=status.HTTP_200_OK
                    )



class Deposit(APIView):
    permission_classes = [IsAuthenticated]
    # throttle_classes = [UserRateThrottle]

    def post(self, request):
        header = {
            'accept': 'application/json',
            'content-type': 'application/json'
        }

        if 'orders' in request.data:
            call_back = '',
        else:
            call_back = ''
    
        data = {
            'merchant_id': '',
            'amount': request.data['amount']*10,
            # 'callback_url': str(call_back),
            'callback_url': '',
            'description': 'test'
        }
        
        
        r = requests.post(url='https://api.zarinpal.com/pg/v4/payment/request.json',
                          json=data,
                          headers=header)
        
        authority = r.json()['data']['authority']

        
        if r.status_code == 200:
            obj = Transaction.objects.create(wallet_id=request.user.wallet.id,
                                             amount=request.data['amount']*10,
                                             transaction_code=authority,
                                             )
            
            cache.set(f'wallet{request.user.wallet.id}', request.data, 600)

            link = f'https://www.zarinpal.com/pg/StartPay/{authority}' 

            return Response(response_func(
                True,
                "gateway link",
                link
            ), status=status.HTTP_200_OK
            )
            


class PaymentCallBack(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            obj = Transaction.objects.get(transaction_code=str(request.GET['Authority']))
            cache_data = cache.get(f'wallet{obj.wallet.id}')
            if cache_data != None:
            
                
                header = {
                    'accept': 'application/json',
                    'content-type': 'application/json'
                }
                
                data = {
                    'merchant_id': '',
                    'amount': obj.amount,
                    'authority': obj.transaction_code
                }
                
                r = requests.post(url='https://api.zarinpal.com/pg/v4/payment/verify.json',
                                json=data, 
                                headers=header)
                try:
                    if r.json()['data']['code'] == 100: 
                        
                        order_id = []
                        for i in cache_data['orders']:
                            order_id.append(i['orderId'])

                        order_obj = Order.objects.filter(id__in=order_id).select_related('customer', 'expert', 'service')

                        obj.wallet.deposit(cache_data['amount']*10)
                        obj.payment_status = 1
                        obj.save()
                        

                        for i in order_obj:

                            for j in cache_data['orders']:

                                if i.id == j['orderId']:

                                    i.how_to_pay = j['method']
                                    i.save()
                except:
                        print("wrong")
                    
                return HttpResponseRedirect()
            
            else:
                return Response(response_func(
                    False,
                    "time expired",
                    {}
                ), status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(response_func(
                False,
                "",
                {"error": str(e)}
            ), status=status.HTTP_400_BAD_REQUEST
            )



class WalletCallBack(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        obj = Transaction.objects.get(transaction_code=request.GET['Authority'])
        header = {
                    'accept': 'application/json',
                    'content-type': 'application/json'
                }
                
        data = {
                    'merchant_id': '',
                    'amount': obj.amount,
                    'authority': obj.transaction_code
                }

        r = requests.post(url='https://api.zarinpal.com/pg/v4/payment/verify.json',
                                json=data, 
                                headers=header)

        try:
            if r.json()['data']['code'] == 100:
                obj.payment_status = 1
                obj.wallet.deposit(int(obj.amount))
                obj.save()
            
        except:
            print("wrong")
        return HttpResponseRedirect()

        
        

class ShabaRegistration(GenericAPIView):
    # permission_classes = (IsAuthenticated,)
    serializer_class = ShabaSerializer

    def get(self, request):
        try:
            obj = Shaba.objects.get(wallet_id=request.user.wallet.id)
            serializer = self.serializer_class(obj)

            

            return Response(response_func(
                                    True,
                                    'OK',
                                    serializer.data
                                    ), status=status.HTTP_200_OK
                            )
        
        except:
            return Response(response_func(
                                    True, 
                                    '',
                                    {},
                                    ), status.HTTP_200_OK
                                )


    def post(self, request):
        serializer = ShabaPostSerializer(data=request.data)

        
        if serializer.is_valid():
                active_link = get_random_string(length=72, allowed_chars=allowed_chars)
                wallet_id = request.user.wallet.id


 
                '''
                check if shaba number exists or not
                '''
                # try:
                #     shaba_obj = Shaba.objects.get(wallet_id=wallet_id)
                    

                #     if shaba_obj.shaba_number == serializer.validated_data.get('iban'):

                #         return Response(response_func(
                #             True,
                #             ".شماره شبا قبلا ثبت شده است",
                #             {}
                #         ), status = status.HTTP_200_OK
                #         )
                    
                #     else:
                #         pass
                # except:
                #     pass


                cache_data = {
                            'wallet_id': wallet_id,
                            'active_link': active_link,
                            'shaba_number': serializer.validated_data.get('iban'),
                            'bank_name': serializer.validated_data.get('bank'),
                            'full_name': serializer.validated_data.get('name'),
                            }
                
                shaba_cache_data(request.user.id, cache_data)
                second_shaba_cache_data(request.user.id, cache_data)


                mobile = request.user      

                link = f"{IBAN_LINK}{active_link}{request.user.id}"  
                print(link)
                
                
                try:
                    # api = KavenegarAPI(API)
                    # params = {
                    #     'receptor': mobile,
                    #     'template': 'Dosma',
                    #     'token': otp_obj_mobile.otp, 
                    #     'type': 'sms',  # sms vs call
                    # }
                    # response = api.verify_lookup(params)
                    # data = {
                    #     'messageid':response[0]['messageid']
                    # }
                    
                    return Response(response_func(
                                            True,
                                            "لینک تایید شماره شبا ارسال شد.",
                                            {"a": link}                     
                                        ), status=status.HTTP_200_OK
                                    )
                except:
                    return Response(
                                response_func(
                                        True,
                                        'اتصال با سرویس پیامکی ممکن نمی باشد. لطفا مجددا تلاش فرمایید.',
                                        {},
                                    ), status=status.HTTP_200_OK
                                )
            
            
        return Response(
                    response_func(
                            False, 
                            'شماره شبا نامعتبر یا تکراری می‌باشد.',
                            {str(serializer.errors)},
                        ),
                        status=status.HTTP_400_BAD_REQUEST
                    )
    
    

class LinkVerification(APIView):
    def get(self, request, activeLink):
        
        # access_token = AccessToken(str())
        # user_id = access_token.payload['user_id']
        # print(user_id)
        try:
            user_id = activeLink[72:]
            active_link = activeLink[:72]

            data = cache.get(f'shaba_data{user_id}') # 3min
            wallet_id = data['wallet_id']

            link = get_random_string(72)
            url = callback_url_for_shaba(link, wallet_id)



        
            if data is not None:     
                if data['active_link'] == active_link:
                    try:
                        shaba_obj, shaba_bool = Shaba.objects.get_or_create(wallet_id=wallet_id)

                        
                        shaba_obj.active_link = data['active_link']
                        shaba_obj.shaba_number = data['shaba_number']
                        shaba_obj.full_name = data['full_name']
                        shaba_obj.bank_name = data['bank_name']
                        shaba_obj.save()



                        
                    # variables = {
                    #     'iban': "",
                    #     'is_legal': False,
                    #     'type': 'SHARE'
                    # }                
                    
                    # header = {
                    #         'Accept': 'application/json',
                    #         'Authorization': ZARINPAL_TOKEN
                    #             }
                        
                    # r = requests.post(url="https://next.zarinpal.com/api/v4/graphql",
                    #                 json={'query': SIGN_UP_QUERY, 'variables': variables},
                    #                 headers=header)
                        

                        

                        access_token = RefreshToken.for_user(shaba_obj.wallet.user)

                        cache.delete(f'shaba_data{user_id}')
                        cache.delete_many([f'shaba_data{user_id}', f'shaba_data_{user_id}'])

                        
                        return HttpResponseRedirect(url)
                    
                    
                    except Exception as e:
                        return Response(response_func(
                                                True,
                                                "",
                                                {}
                        ), status=status.HTTP_400_BAD_REQUEST
                        )
                    
                
                return HttpResponseRedirect(url)
                
            return Response(response_func(
                                    True,
                                    "لینک منقضی شده است. لطفا دوباره تلاش فرمایید.",
                                    {},
                                    ), status=status.HTTP_400_BAD_REQUEST
                                    )
        
        except Exception as e:
            return HttpResponseRedirect()


class ShabaData(GenericAPIView):
    serializer_class = ShabaDataSerializer


    def get(self, request, activeLink):
        try:
            wallet_id = activeLink[72:]

            obj = Shaba.objects.get(wallet_id=wallet_id)
            serializer = self.serializer_class(obj)


            return Response(response_func(
                                    True,
                                    "",
                                    serializer.data
                    ), status=status.HTTP_200_OK
                )
        
        except Exception as e:
            return Response(response_func(
                                    False,
                                    "",
                                    {}
            ), status=status.HTTP_200_OK
            )
        



class LoadingPage(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        data = cache.get(f"shaba_data{request.user.id}")
        data1 = cache.get(f"shaba_data_{request.user.id}")

    
        
        if data is None and data1 is None:
            return Response(response_func(
                                    True,
                                    "",
                                    {"acceptance": True}
            ), status=status.HTTP_200_OK
            )
        
        else:
            return Response(response_func(
                                    True,
                                    "",
                                    {"acceptance": False}
            ), status=status.HTTP_200_OK
            )
            
        
        


class ShabaCancel(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self, request):

        user_id = request.user.id
        cache.delete_many([f"shaba_data{user_id}", f"shaba_data_{user_id}"])

        return Response(response_func(
                                True,
                                "",
                                {}
                            ), status=status.HTTP_200_OK
                            )


        



class SendLinkAgain(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        first_data = cache.get(f"shaba_data{request.user.id}")
        second_data = cache.get(f"shaba_data_{request.user.id}")
        

        if first_data is not None:
            return Response(response_func(
                                    False,
                                    "لینک قبلی هنوز معتبر است",
                                    {}
                                ), status = status.HTTP_400_BAD_REQUEST
                            )
        
        else:
            if second_data is not None:
                print("ss")

                active_link = get_random_string(72, allowed_chars=allowed_chars)
                print(second_data)



                second_data['active_link'] = active_link
                user_id = request.user.id

                shaba_cache_data(user_id, second_data)
                # print(link)


                try:
                    # api = KavenegarAPI(API)
                    # params = {
                    #     'receptor': mobile,
                    #     'template': 'Dosma',
                    #     'token': otp_obj_mobile.otp, 
                    #     'type': 'sms',  # sms vs call
                    # }
                    # response = api.verify_lookup(params)
                    # data = {
                    #     'messageid':response[0]['messageid']
                    # }
                    return Response(response_func(
                                            True,
                                            "لینک دوباره ارسال شد",
                                            {
                                                'a': IBAN_LINK + active_link
                                            #    'messageid':response[0]['messageid']
                                            }     
                                        ), status=status.HTTP_200_OK
                                    )
                except:
                    return Response(response_func(
                                            False,
                                            "اتصال با سرویس پیامکی ممکن نمی باشد. لطفا مجددا تلاش فرمایید.",
                                            {}
                                        ), status = status.HTTP_400_BAD_REQUEST
                                    )
            return redirect(reverse('wallets:shaba-registration'))
        
        # return redirect(reverse("wallets:shaba-registration"))
        


        
class ImmediateCheckout(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            shaba = Shaba.objects.get(wallet_id=request.user.wallet.id)
            block_money = account_models.ExpertSkill.objects.get(user_id=request.user.id).block_money
            
            
            header = {
                    'Accept': 'application/json',
                    'Authorization': ZARINPAL_TOKEN
                }
            
            query1 = '''query{
                    BankAccounts(limit: 500) {
                        id
                        iban
                        holder_name
                    }
                        }'''
                    
            query = '''
                    mutation InstantPayoutAdd(
                        $terminal_id: ID!, 
                        $bank_account_id: ID!, 
                        $amount: BigInteger!) {
                    resource: InstantPayoutAdd(
                    terminal_id: $terminal_id, 
                    bank_account_id: $bank_account_id, 
                    amount: $amount) {
                        id
                        url_code
                        status
                        amount
                        fee
                        created_at
                    }
                }
            '''
            
        
            r = requests.post(url="https://next.zarinpal.com/api/v4/graphql",
                              json={'query': query1}, 
                              headers=header)
            
            
            for i in r.json()['data']['BankAccounts']:
                if shaba.shaba_number == i['iban'][2:]:
                    if request.data['amount'] <= shaba.wallet.total_balance - block_money:
                    
                        var = {
                                "terminal_id": "384455",
                                "bank_account_id": i['id'],
                                "amount": request.data['amount']
                            }
                    
                        r = requests.post(
                                          url="https://next.zarinpal.com/api/v4/graphql",
                                          json={'query': query, 'variables': var}, 
                                          headers=header
                                          )
                        
                        
                        return Response(response_func(
                                                True,
                                                "تسویه حساب با موفقیت ثبت شد",
                                                {}
                                            ), status=status.HTTP_200_OK
                                                )
                        
                    else:
                        return Response(response_func(
                                                False,
                                                'مبلغ ورودی بیشتر از موجودی است',
                                                {}
                                            ), status=status.HTTP_400_BAD_REQUEST
                                                )
                        
                else:
                    return Response(response_func(
                                            False,
                                            '',
                                            {}
                                        ), status=status.HTTP_400_BAD_REQUEST
                                            )
                    
            return Response("sadas")
               

        except Exception as e:
            return Response(response_func(
                                    False,
                                    "",
                                    {"error": str(e)}
                                ), status=status.HTTP_400_BAD_REQUEST
                                    )
            