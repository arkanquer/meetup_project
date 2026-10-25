from django.contrib import admin
from .models import Venue, Friendship, Proposal, Application, Message, Review

admin.site.register(Venue)
admin.site.register(Friendship)
admin.site.register(Proposal)
admin.site.register(Application)
admin.site.register(Message)
admin.site.register(Review)