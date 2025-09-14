import logging
from django.conf import settings
from django.db.models import Sum
from .models import ProductListing, FarmerGroup, Offer
from users.models import User
# from langchain_google_genai import GoogleGenerativeAIEmbeddings # For embeddings if needed

# If using django-background-tasks
from background_task import background
# If using Celery, import app from your celery.py
# from kisan_mitra.celery import app as celery_app

logger = logging.getLogger(__name__)

# Mock function for embedding (replace with actual)
def get_embedding(text):
    # embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=settings.GEMINI_API_KEY)
    # return embeddings_model.embed_query(text)
    return [hash(text) % 1000 for _ in range(10)] # Placeholder

# --- AI Unity Leader Tasks ---

# @celery_app.task # If using Celery
@background(schedule=60*60) # Run every hour (or tune frequency)
def group_similar_listings():
    logger.info("Starting task: group_similar_listings")
    active_listings = ProductListing.objects.filter(is_active=True, farmer_groups__isnull=True) # Un-grouped active listings

    # 1. Generate embeddings for all ungrouped products
    # This might be done when listing is created too. If not, do it here.
    for listing in active_listings:
        if not listing.embedding:
            # Generate descriptive text based on product name, expected price, etc.
            description_text = f"{listing.product_name} from {listing.location_pin_code} at {listing.price_expectation_per_kg} per kg."
            listing.embedding = get_embedding(description_text)
            listing.save()
            
    # Re-fetch with embeddings
    active_listings_with_embeddings = ProductListing.objects.filter(is_active=True, farmer_groups__isnull=True).exclude(embedding__isnull=True)

    # 2. Iterate and group based on similarity (simplified for concept)
    grouped_listing_ids = set()
    for listing1 in active_listings_with_embeddings:
        if listing1.id in grouped_listing_ids:
            continue

        potential_group = [listing1]
        grouped_listing_ids.add(listing1.id)

        # Simple similarity: same product name and nearby pin codes
        # In actual implementation: use vector similarity search (pgvector)
        for listing2 in active_listings_with_embeddings:
            if listing1.id == listing2.id or listing2.id in grouped_listing_ids:
                continue
            
            # Simple criteria for grouping: same product name and within a few km (logic for 'nearby' needed)
            if listing1.product_name == listing2.product_name and \
               abs(int(listing1.location_pin_code) - int(listing2.location_pin_code)) < 100 : # Very simplistic 'nearby'
                
                # More advanced: calculate cosine similarity between embeddings
                # similarity = calculate_cosine_similarity(listing1.embedding, listing2.embedding)
                # if similarity > THRESHOLD:
                potential_group.append(listing2)
                grouped_listing_ids.add(listing2.id)

        if len(potential_group) > 1: # Create a group if more than one listing
            total_quantity = sum(x.quantity_kg for x in potential_group)
            
            # Elect a leader: e.g., the farmer with the largest quantity in the group
            leader = max(potential_group, key=lambda x: x.quantity_kg).farmer

            group_name = f"Group for {listing1.product_name} - {total_quantity}kg"
            new_group = FarmerGroup.objects.create(
                leader=leader,
                group_name=group_name,
                total_quantity_kg=total_quantity,
                status='active'
            )
            new_group.products.set(potential_group)
            
            # Notify farmers in the group (e.g., via email or in-app notification)
            for listing in potential_group:
                logger.info(f"Notifying {listing.farmer.username} about new group: {new_group.group_name}")
                # You'd send actual notifications here.

    logger.info("Finished task: group_similar_listings")

# @celery_app.task # If using Celery
@background(schedule=0) # Run immediately or on condition
def process_offer_votes(offer_id):
    logger.info(f"Processing votes for offer {offer_id}")
    offer = Offer.objects.get(id=offer_id)
    group = offer.group
    
    # Get all farmers in the group
    group_farmers = User.objects.filter(id__in=group.products.values_list('farmer_id', flat=True)).distinct()
    total_voters = group_farmers.count()

    accept_votes = offer.votes.filter(vote='accept').count()
    reject_votes = offer.votes.filter(vote='reject').count()
    counter_votes = offer.votes.filter(vote='counter').count()

    # Define majority threshold (e.g., 60% of group farmers must accept)
    if total_voters > 0 and accept_votes / total_voters >= 0.6: # configurable threshold
        offer.status = 'accepted'
        group.status = 'deal_closed'
        offer.save()
        group.save()
        logger.info(f"Offer {offer_id} accepted for group {group.id}.")
        # Trigger supply chain optimization
        trigger_supply_chain_optimization.now(offer.id)
    elif reject_votes > 0: # If at least one farmer explicitly rejects
        offer.status = 'rejected'
        offer.save()
        logger.info(f"Offer {offer_id} rejected for group {group.id}.")
    elif counter_votes > 0:
        offer.status = 'countered'
        offer.save()
        logger.info(f"Offer {offer_id} countered for group {group.id}. Leader should review.")
    else:
        logger.info(f"Offer {offer_id} still pending votes for group {group.id}.")
    
    # Notifications to buyer/farmers about offer status change would go here.

# @celery_app.task
@background(schedule=0)
def trigger_supply_chain_optimization(offer_id):
    logger.info(f"Starting supply chain optimization for offer {offer_id}")
    offer = Offer.objects.get(id=offer_id)
    group = offer.group

    # Collect locations of all farmers in the group
    farmer_locations = []
    for listing in group.products.all():
        if listing.farmer.pin_code:
            farmer_locations.append(listing.farmer.pin_code) # or lat/lon if available

    buyer_location = offer.buyer.pin_code if offer.buyer.pin_code else None

    # Call a function to hit Google Maps API
    # This involves complex logic to find optimal meeting points/routes
    # For conceptual:
    meeting_point = "Example Central Location"
    optimal_route_data = {"route_coords": "dummy_geojson"}
    estimated_cost = 500.00

    # Save logistics details
    logistics, created = SupplyChainLogistics.objects.get_or_create(offer=offer, group=group)
    # logistics.meeting_point_lat = ... # Resolve from Google Maps
    # logistics.meeting_point_lon = ...
    logistics.optimal_route_json = optimal_route_data
    logistics.estimated_costs = estimated_cost
    logistics.save()
    logger.info(f"Supply chain optimized for offer {offer_id}. Meeting point: {meeting_point}")

    # Notify all parties