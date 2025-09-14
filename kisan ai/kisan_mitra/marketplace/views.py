from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import ProductListing, FarmerGroup, Offer, OfferVote
from .forms import ProductListingForm, OfferForm, OfferVoteForm
from .tasks import process_offer_votes # Import the background task

def is_farmer(user):
    return user.is_authenticated and user.user_type == 'farmer'

def is_buyer(user):
    return user.is_authenticated and user.user_type == 'buyer'

@login_required
@user_passes_test(is_farmer)
def create_listing(request):
    if request.method == 'POST':
        form = ProductListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.farmer = request.user
            listing.location_pin_code = request.user.pin_code # Default from profile
            listing.save()
            return redirect('farmer_dashboard') # Or listing detail
    else:
        form = ProductListingForm()
    return render(request, 'marketplace/listing_form.html', {'form': form})

@login_required
def view_product_groups(request):
    groups = FarmerGroup.objects.filter(status='active').prefetch_related('products', 'leader')
    return render(request, 'marketplace/group_list.html', {'groups': groups})

@login_required
@user_passes_test(is_buyer)
def make_offer(request, group_id):
    group = get_object_or_404(FarmerGroup, id=group_id)
    if request.method == 'POST':
        form = OfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.group = group
            offer.buyer = request.user
            offer.save()
            # Notify group leader or members about the new offer
            return redirect('buyer_dashboard')
    else:
        form = OfferForm(initial={'offered_quantity_kg': group.total_quantity_kg})
    return render(request, 'marketplace/make_offer.html', {'form': form, 'group': group})

@login_required
@user_passes_test(is_farmer)
def review_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    # Ensure this farmer is part of the group for this offer
    if not offer.group.products.filter(farmer=request.user).exists() and offer.group.leader != request.user:
        return JsonResponse({'error': 'Not authorized to vote on this offer'}, status=403)

    if request.method == 'POST':
        form = OfferVoteForm(request.POST)
        if form.is_valid():
            try:
                vote = OfferVote.objects.create(
                    offer=offer,
                    farmer=request.user,
                    vote=form.cleaned_data['vote'],
                    comment=form.cleaned_data.get('comment')
                )
                # Trigger the background task to re-evaluate offer status after a vote
                process_offer_votes.now(offer.id) # .now() runs synchronously for testing/immediate trigger
                                                # For production, use .delay() with Celery or .schedule() with django-background-tasks
                return JsonResponse({'message': 'Vote recorded successfully!'})
            except Exception as e:
                return JsonResponse({'error': f'Failed to record vote: {e}'}, status=400)
        else:
            return JsonResponse({'errors': form.errors}, status=400)
    else: # GET request
        # Display the offer details and voting options
        user_vote = OfferVote.objects.filter(offer=offer, farmer=request.user).first()
        form = OfferVoteForm(initial={'vote': user_vote.vote if user_vote else None})
        return render(request, 'marketplace/review_offer.html', {'offer': offer, 'form': form, 'user_vote': user_vote})