from django.core.cache import cache

def shaba_cache_data(user_id: int, data: dict):
    cache.set(f"shaba_data{user_id}", data, 10)



def second_shaba_cache_data(user_id: int, data: dict):
    cache.set(f"shaba_data_{user_id}", data, 30)




def callback_url_for_shaba(link, wallet_id):
    return f"http://192.168.1.177:3000/shaba-success/{link}{wallet_id}/"


    




