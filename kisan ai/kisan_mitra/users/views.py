from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import UserRegistrationForm, FarmerProfileForm, BuyerProfileForm

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])
            user.save()

            if user.user_type == 'farmer':
                profile_form = FarmerProfileForm(request.POST, instance=FarmerProfile(user=user))
                if profile_form.is_valid():
                    profile_form.save()
            elif user.user_type == 'buyer':
                profile_form = BuyerProfileForm(request.POST, instance=BuyerProfile(user=user))
                if profile_form.is_valid():
                    profile_form.save()
            
            login(request, user) # Auto-login after registration
            return redirect('dashboard') # Redirect to user's dashboard

    else:
        user_form = UserRegistrationForm()
        farmer_profile_form = FarmerProfileForm()
        buyer_profile_form = BuyerProfileForm()
    
    return render(request, 'users/register.html', {
        'user_form': user_form,
        'farmer_profile_form': farmer_profile_form,
        'buyer_profile_form': buyer_profile_form
    })