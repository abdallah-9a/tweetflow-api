from celery import shared_task
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from tweets.models import Tweet
from interactions.models import Mention
import re

User = get_user_model()

@shared_task
def parse_mentions_task(tweet_id):
    try:
        tweet = Tweet.objects.get(id=tweet_id)
    except Tweet.DoesNotExist:
        return

    if not tweet.content:
        return

    pattern = r"@(\w+)"
    usernames = re.findall(pattern, tweet.content)

    if not usernames:
        return

    content_type = ContentType.objects.get_for_model(Tweet)
    usernames = set(usernames)
    mentioned_users = User.objects.filter(username__in=usernames)
    
    for user in mentioned_users:
        if user != tweet.user:
            Mention.objects.get_or_create(
                actor=tweet.user,
                mentioned_user=user,
                content_type=content_type,
                content_id=tweet.id,
            )
