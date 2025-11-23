from django.contrib import admin
from .models import Tweet, Like, Comment, Retweet, Bookmark

# Register your models here.

admin.site.register(Tweet)
admin.site.register(Retweet)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Bookmark)
