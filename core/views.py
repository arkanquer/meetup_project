from datetime import timedelta
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Q
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import ProposalForm
from .models import Application, Friendship, Proposal, ProposalMessage, Rating, Venue


def home_page(request):
    Proposal.objects.filter(
        status="active",
        proposed_time__lt=timezone.now()
    ).update(status="closed")

    proposals = Proposal.objects.filter(status="active")
    return render(request, "core/home_page.html", {"proposals": proposals})


@login_required
def profile_view(request):
    current_filter = request.GET.get('filter', 'all')

    my_proposals = Proposal.objects.filter(creator=request.user).order_by('-created_at')
    my_joined_proposals = Application.objects.filter(
        possible_guest=request.user,
        status="accepted",
    ).exclude(proposal__creator=request.user)

    if current_filter == 'active':
        my_proposals = my_proposals.filter(status='active')
        my_joined_proposals = my_joined_proposals.filter(proposal__status='active')
    elif current_filter == 'closed':
        my_proposals = my_proposals.filter(status='closed')
        my_joined_proposals = my_joined_proposals.filter(proposal__status='closed')
    friend_requests = Friendship.objects.filter(friend=request.user, status='pending')
    active_friendships = Friendship.objects.filter(
        Q(creator=request.user) | Q(friend=request.user),
        status='accepted'
    )

    return render(request, 'core/profile.html', {
        'my_created_proposals': my_proposals,
        'my_joined_apps': my_joined_proposals,
        'current_filter': current_filter,
        'friend_requests': friend_requests,
        'active_friendships': active_friendships,
    })

@login_required
def create_proposal(request):
    if request.method == 'POST':
        form = ProposalForm(request.POST)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.creator = request.user

            new_event_time = form.cleaned_data.get('proposed_time')
            if new_event_time:
                min_time = new_event_time - timedelta(hours=6)
                max_time = new_event_time + timedelta(hours=6)

                collision_exists = Proposal.objects.filter(
                    creator=request.user,
                    status='active',
                    proposed_time__range=(min_time, max_time)
                ).exists()

                if collision_exists:
                    form.add_error('proposed_time',
                                   "Накладка в розкладі: між вашими зустрічами має бути перерва не менше 6 годин.")
                    return render(request, 'core/create_proposal.html', {'form': form})

            v_name = request.POST.get('venue_name')
            v_address = request.POST.get('venue_address')
            if v_name:
                venue, _ = Venue.objects.get_or_create(name=v_name, address=v_address)
                proposal.venue = venue

            proposal.save()
            return redirect('home')
    else:
        form = ProposalForm()

    return render(request, 'core/create_proposal.html', {'form': form})


@login_required
def close_proposal(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    if proposal.creator == request.user:
        proposal.status = 'closed'
        proposal.save()
    return redirect('home')

def proposal_details(request, pk):
    proposal_dtls = get_object_or_404(Proposal, pk=pk)
    application_dtls = proposal_dtls.application_proposal.all()

    user_application = None
    is_already_busy = False
    friendship_status = None

    if request.user.is_authenticated:
        user_application = proposal_dtls.application_proposal.filter(possible_guest=request.user).first()

        is_already_busy = Application.objects.filter(
            possible_guest=request.user,
            status='accepted',
            proposal__status='active'
        ).exclude(proposal=proposal_dtls).exists()
        friendship_status = Friendship.objects.filter(
            (Q(creator=request.user) & Q(friend=proposal_dtls.creator)) |
            (Q(creator=proposal_dtls.creator) & Q(friend=request.user))
        ).first()

    context = {
        'proposal_dtls': proposal_dtls,
        'application_dtls': application_dtls,
        'user_application': user_application,
        'is_already_busy': is_already_busy,
        'friendship_status': friendship_status,
    }
    return render(request, 'core/proposal_details.html', context)


@login_required
def send_application(request, pk):
    proposal_x = get_object_or_404(Proposal, pk=pk)
    if proposal_x.creator != request.user:
        already_busy = Application.objects.filter(
            possible_guest=request.user,
            status='accepted',
            proposal__status='active'
        ).exists()
        if not already_busy:
            Application.objects.get_or_create(
                proposal=proposal_x,
                possible_guest=request.user,
            )
    return redirect('proposal_details', pk=pk)


@login_required
def accept_application(request, pk):
    application_x = get_object_or_404(Application, pk=pk)
    if application_x.proposal.creator == request.user:
        application_x.status = "accepted"
        application_x.save()
    return redirect('proposal_details', pk=application_x.proposal.id)

@login_required
def reject_application(request, pk):
    application_x = get_object_or_404(Application, pk=pk)
    if application_x.proposal.creator == request.user:
        application_x.status = "declined"
        application_x.save()
    return redirect('proposal_details', pk=application_x.proposal.id)

@login_required
def remove_guest(request, pk):
    application_i = get_object_or_404(Application, pk=pk)
    proposal_id = application_i.proposal.id
    if application_i.proposal.creator == request.user:
        application_i.delete()
    return redirect('proposal_details', pk=proposal_id)


@login_required
def proposal_chat(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    is_creator = (proposal.creator == request.user)
    is_accepted_guest = proposal.application_proposal.filter(possible_guest=request.user, status='accepted').exists()
    if not (is_creator or is_accepted_guest):
        raise PermissionDenied
    if request.method == 'POST':
        message_text = request.POST.get('message_text', '').strip()
        if message_text:
            ProposalMessage.objects.create(
                proposal=proposal,
                sender=request.user,
                text=message_text
            )
            return redirect('proposal_chat', pk=proposal.id)
    messages = proposal.chat_messages.all()
    return render(request, 'core/proposal_chat.html', {
        'proposal': proposal,
        'chat_messages': messages
    })

@login_required
def send_friend_request(request, user_id):
    to_user = get_object_or_404(User, pk=user_id)
    if to_user != request.user:
        inverse_request_exists = Friendship.objects.filter(
            creator=to_user,
            friend=request.user
        ).exists()

        if not inverse_request_exists:
            Friendship.objects.get_or_create(
                creator=request.user,
                friend=to_user,
            )
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def accept_friend_request(request, request_id):
    friendship = get_object_or_404(Friendship, pk=request_id)
    if friendship.friend == request.user and friendship.status == 'pending':
        friendship.status = 'accepted'
        friendship.save()
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def reject_or_remove_friend(request, request_id):
    friendship = get_object_or_404(Friendship, pk=request_id)
    if friendship.creator == request.user or friendship.friend == request.user:
        friendship.delete()
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def rate_user(request, user_id):
    if request.method == 'POST':
        to_user = get_object_or_404(User, pk=user_id)
        score = request.POST.get('score')
        if score and to_user != request.user:
            Rating.objects.update_or_create(
                from_user=request.user,
                to_user=to_user,
                defaults={'score': int(score)}
            )
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def top_users(request):
    leaders = User.objects.annotate(
        avg_rating=Coalesce(Avg('received_ratings__score'), 0.0)
    ).order_by('-avg_rating')[:10]
    return render(request, 'core/top_users.html', {'leaders': leaders})

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')