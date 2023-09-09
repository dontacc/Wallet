import string


PAYMENT_STATUS = (
    (0, "ناموفق"),
    (1, "موفق")
)

TITLE_STATUS = (
    (0, "برداشت"),  # bardasht az wallet
    (1, "پرداخت")  # pardakht be wallet
)

TRANSACTION_STATUS_CHOICES = (
    (0, "افزایش موجودی"),  # deposit
    (1, "کاهش از موجودی کیف پول برای هزینه سفارش"),  # for costumer
    (2, "درآمد, پرداخت به صورت آنلاین"),  # kam shodane komision 10% + va 9% maliat az daramad va bad pardakht be wallet
    (3, "کاهش از موجودی حساب متخصص برای پرداخت های نقدی"),
    (4, "کاهش بابت عوارض مالیات"),
    (5, "تسویه حساب"), # az tarighe shaba enteghale mojodi be hesabe bankish faghat male experte
)



lower_case = string.ascii_lowercase
camel_case = string.ascii_uppercase

allowed_chars = f"1234567890{lower_case}{camel_case}"