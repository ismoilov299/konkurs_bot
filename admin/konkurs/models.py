from django.db import models
from django.core.validators import MinValueValidator

class Award(models.Model):
    """Mukofotlar uchun model"""
    title = models.CharField(max_length=200, verbose_name="Nomi")
    description = models.TextField(verbose_name="Tavsif")
    image = models.ImageField(
        upload_to='awards/images/',
        verbose_name="Rasm"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    class Meta:
        verbose_name = "Mukofot"
        verbose_name_plural = "Mukofotlar"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class User(models.Model):
    """Foydalanuvchilar uchun model"""
    fullname = models.CharField(max_length=255, verbose_name="To'liq ism")
    telegram_id = models.BigIntegerField(
        unique=True,
        verbose_name="Telegram ID"
    )
    username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Telegram username"
    )
    score = models.IntegerField(
        default=0,
        verbose_name="Ballar",
        validators=[MinValueValidator(0)]
    )
    referral_code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Referal kod"
    )
    referred_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals',
        verbose_name="Kim tomonidan taklif qilingan"
    )
    is_referral_counted = models.BooleanField(
        default=False,
        verbose_name="Referal ball berilganmi"
    )
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.fullname} ({self.score} ball)"

class Link(models.Model):
    """Kanallar va linklar uchun model"""
    title = models.CharField(max_length=255, verbose_name="Nomi")
    url = models.URLField(verbose_name="URL manzil")
    subscribers = models.ManyToManyField(
        User,
        through='UserSubscription',
        related_name='subscribed_channels',
        verbose_name="Obuna bo'lganlar"
    )
    is_required = models.BooleanField(
        default=True,
        verbose_name="Majburiy obuna"
    )
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kanal"
        verbose_name_plural = "Kanallar"
        ordering = ['title']

    def __str__(self):
        return self.title

    @property
    def subscriber_count(self):
        return self.usersubscription_set.filter(is_subscribed=True).count()

class UserSubscription(models.Model):
    """Foydalanuvchi obunalarini kuzatish uchun model"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Foydalanuvchi"
    )
    channel = models.ForeignKey(
        Link,
        on_delete=models.CASCADE,
        verbose_name="Kanal"
    )
    is_subscribed = models.BooleanField(
        default=False,
        verbose_name="Obuna holati"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Obuna"
        verbose_name_plural = "Obunalar"
        unique_together = ['user', 'channel']

    def __str__(self):
        return f"{self.user.fullname} - {self.channel.title}"

class Statistics(models.Model):
    """Statistika uchun model"""
    date = models.DateField(
        auto_now_add=True,
        verbose_name="Sana"
    )
    total_users = models.IntegerField(
        default=0,
        verbose_name="Jami foydalanuvchilar"
    )
    active_users = models.IntegerField(
        default=0,
        verbose_name="Faol foydalanuvchilar"
    )
    total_subscriptions = models.IntegerField(
        default=0,
        verbose_name="Jami obunalar"
    )
    total_score = models.IntegerField(
        default=0,
        verbose_name="Jami ballar"
    )
    referral_counts = models.IntegerField(
        default=0,
        verbose_name="Referal hisoblanganlar"
    )

    class Meta:
        verbose_name = "Statistika"
        verbose_name_plural = "Statistikalar"
        ordering = ['-date']

    def __str__(self):
        return f"Statistika: {self.date}"

    def update_statistics(self):
        """Statistikani yangilash"""
        self.total_users = User.objects.count()
        self.active_users = User.objects.filter(is_active=True).count()
        self.total_subscriptions = UserSubscription.objects.filter(
            is_subscribed=True
        ).count()
        self.total_score = User.objects.aggregate(
            total=models.Sum('score')
        )['total'] or 0
        self.referral_counts = User.objects.filter(
            is_referral_counted=True
        ).count()
        self.save()

