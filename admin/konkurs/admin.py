from django.contrib import admin
from django.utils.html import format_html
from .models import Award, User, Link, UserSubscription, Statistics


@admin.register(Award)
class AwardAdmin(admin.ModelAdmin):
    list_display = ('title', 'display_image', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description')

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "Rasm yo'q"

    display_image.short_description = 'Rasm'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('fullname', 'telegram_id', 'username', 'score',
                    'referral_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'is_referral_counted', 'created_at')
    search_fields = ('fullname', 'telegram_id', 'username', 'referral_code')
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('fullname', 'telegram_id', 'username', 'score')
        }),
        ('Referal tizimi', {
            'fields': ('referral_code', 'referred_by', 'is_referral_counted')
        }),
        ('Qo\'shimcha', {
            'fields': ('is_active',)
        }),
    )

    def referral_count(self, obj):
        return obj.referrals.count()

    referral_count.short_description = 'Referallar soni'


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'subscriber_count', 'is_required',
                    'is_active', 'created_at')
    list_filter = ('is_required', 'is_active', 'created_at')
    search_fields = ('title', 'url')


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'channel', 'is_subscribed', 'created_at')
    list_filter = ('is_subscribed', 'created_at')
    search_fields = ('user__fullname', 'channel__title')
    raw_id_fields = ('user', 'channel')


@admin.register(Statistics)
class StatisticsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_users', 'active_users',
                    'total_subscriptions', 'total_score', 'referral_counts')
    list_filter = ('date',)
    readonly_fields = ('total_users', 'active_users', 'total_subscriptions',
                       'total_score', 'referral_counts')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# Admin sayt sarlavhasi va headerini o'zgartirish
admin.site.site_header = "Bot Boshqaruv Paneli"
admin.site.site_title = "Bot Admin"
admin.site.index_title = "Bot Boshqaruvi"