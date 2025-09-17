# store/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Address, ContactMessage 

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'cpf')

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        exclude = ('user',) # Exclui o campo de usuário do formulário
        
        # Define os rótulos personalizados em português
        labels = {
            'street': 'Rua / Logradouro',
            'number': 'Número',
            'complement': 'Complemento (Opcional)',
            'neighborhood': 'Bairro',
            'city': 'Cidade',
            'state': 'Estado (UF)',
            'zip_code': 'CEP',
        }

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']