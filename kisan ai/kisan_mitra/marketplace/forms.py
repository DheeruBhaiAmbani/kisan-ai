from django import forms
from .models import ProductListing, Offer, OfferVote

class ProductListingForm(forms.ModelForm):
    class Meta:
        model = ProductListing
        fields = ['product_name', 'quantity_kg', 'price_expectation_per_kg', 'available_from', 'available_until']
        widgets = {
            'available_from': forms.DateInput(attrs={'type': 'date'}),
            'available_until': forms.DateInput(attrs={'type': 'date'}),
        }

class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ['offered_price_per_kg', 'offered_quantity_kg', 'delivery_terms']

class OfferVoteForm(forms.Form):
    vote_choices = [
        ('accept', 'Accept'),
        ('reject', 'Reject'),
        ('counter', 'Counter')
    ]
    vote = forms.ChoiceField(choices=vote_choices, widget=forms.RadioSelect)
    comment = forms.CharField(widget=forms.Textarea, required=False)