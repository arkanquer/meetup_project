from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg

def get_rating(self):
    avg = self.received_ratings.aggregate(Avg('score'))['score__avg']
    return round(avg, 1) if avg else "—"

User.add_to_class('get_rating', get_rating)

class Rating(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    score = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user') # Один користувач може оцінити іншого лише один раз

    def __str__(self):
        return f"Від @{self.from_user.username} до @{self.to_user.username}: {self.score}"

class Venue(models.Model):
    CATEGORIES =[
        ("cinema", "Кінотеатр"),
        ("theatre", "Театр"),
        ("club", "Клуб"),
        ("billiards", "Більярд"),
    ]
    name = models.CharField(max_length=150, verbose_name="Назва закладу")
    address = models.CharField(max_length=255, verbose_name="Адреса")
    category = models.CharField(max_length=20, choices=CATEGORIES, verbose_name="Категорія")
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class Friendship(models.Model):
    FRIENDSHIP_REQUESTS = [
        ("accepted", "Прийнято"),
        ("declined", "Відхилено"),
        ("pending", "Очікування...")
    ]
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friendship_initiated")
    friend = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friendships_received")
    status = models.CharField(max_length=15, choices=FRIENDSHIP_REQUESTS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)


class Proposal(models.Model):
    PROROSALS_STATUSES = [
        ("active", "Активне"),
        ("closed", "Не активне")
    ]
    title = models.CharField(max_length=150, verbose_name="Назва оголошення")
    venue = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True, blank=True, related_name="proposals_venue")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="proposals_creator")
    status = models.CharField(max_length=15, choices=PROROSALS_STATUSES, default='active')
    proposed_time = models.DateTimeField(verbose_name="Час зустрічі")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title


class Application(models.Model):
    STATUS_CHOICES = [
        ("accepted", "Прийнято"),
        ("declined", "Відхилено"),
        ("pending", "Очікування...")
    ]
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name="application_proposal")
    possible_guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name="application_possible_guest")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('proposal', 'possible_guest')
        ordering = ['-created_at']
    def __str__(self):
        return f"Заявка від {self.possible_guest.username} на подію: {self.proposal.title}"

class Message(models.Model):
    STATUS_CHOICES = [
        ("read", "прочитано"),
        ("unread", "непрочитано")
    ]
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="message_sender")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="message_receiver")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="unread")
    created_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField(blank=True)
    def __str__(self):
        return f"Повідомленя від {self.sender.username} для {self.receiver.username} з текстом {self.message}"

class Review(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="review_username")
    reviewed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviewed_username")
    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True)
    rating = models.PositiveIntegerField(verbose_name="Оцінка (1-5)")
    was_present = models.BooleanField(default=True, verbose_name="Чи прийшов(-а) на зустріч?")
    def __str__(self):
        return f"Відгук від {self.reviewer.username} для {self.reviewed_user.username} (Оцінка: {self.rating})"

class ProposalMessage(models.Model):
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name="chat_messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(verbose_name="Повідомлення")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.proposal.title}] {self.sender.username}: {self.text[:20]}"