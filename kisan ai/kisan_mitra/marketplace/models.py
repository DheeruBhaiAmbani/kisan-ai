from django.db import models
from users.models import User # Assuming User model is in users app

class ProductListing(models.Model):
    # Represents a farmer's intention to sell a specific product
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'farmer'})
    product_name = models.CharField(max_length=100)
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    price_expectation_per_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    location_pin_code = models.CharField(max_length=10) # From farmer's profile initially, can be overridden
    listing_date = models.DateTimeField(auto_now_add=True)
    available_from = models.DateField(null=True, blank=True)
    available_until = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    # Optional: vector embedding of product description for AI grouping similarity
    embedding = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.product_name} by {self.farmer.username} ({self.quantity_kg}kg)"

class FarmerGroup(models.Model):
    # Represents a collective of farmers offering similar products
    products = models.ManyToManyField(ProductListing, related_name='farmer_groups')
    leader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'user_type': 'farmer'})
    group_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    total_quantity_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=50, default='active', choices=[('active', 'Active'), ('negotiating', 'Negotiating'), ('deal_closed', 'Deal Closed')])

    def __str__(self):
        return self.group_name

class Offer(models.Model):
    # Represents a buyer's offer on a FarmerGroup's collective produce
    group = models.ForeignKey(FarmerGroup, on_delete=models.CASCADE, related_name='offers')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'buyer'})
    offered_price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    offered_quantity_kg = models.DecimalField(max_digits=10, decimal_places=2) # Buyer might not buy all
    delivery_terms = models.TextField(blank=True)
    offer_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='pending', choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected'), ('countered', 'Countered')])

    def __str__(self):
        return f"Offer from {self.buyer.username} for {self.group.group_name}"

class OfferVote(models.Model):
    # Farmers vote on offers
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='votes')
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'farmer'})
    vote = models.CharField(max_length=20, choices=[('accept', 'Accept'), ('reject', 'Reject'), ('counter', 'Counter')])
    comment = models.TextField(blank=True)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('offer', 'farmer') # A farmer can only vote once per offer

    def __str__(self):
        return f"{self.farmer.username} voted {self.vote} on Offer {self.offer.id}"

class SupplyChainLogistics(models.Model):
    # For supply chain optimization (after deal is closed)
    offer = models.OneToOneField(Offer, on_delete=models.CASCADE, null=True, blank=True)
    farmer_group = models.OneToOneField(FarmerGroup, on_delete=models.CASCADE, related_name='logistics', null=True, blank=True)
    meeting_point_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    meeting_point_lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    optimal_route_json = models.JSONField(blank=True, null=True) # GeoJSON for route
    estimated_costs = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # Could link to delivery agents, vehicles etc.

    def __str__(self):
        return f"Logistics for Group {self.farmer_group.group_name}"