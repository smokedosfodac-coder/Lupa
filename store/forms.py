from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, ContactMessage, Address
from django.contrib.auth.forms import UserChangeForm

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adiciona classes CSS para ficar bonito
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-input'})
        
        # Torna campos obrigatórios
        self.fields['first_name'].required = True
        self.fields['email'].required = True

    # --- VALIDAÇÃO DE E-MAIL ---
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Este e-mail já está sendo utilizado. Tente fazer login.")
        return email

    # --- VALIDAÇÃO DE TELEFONE ---
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and CustomUser.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Este telefone já está cadastrado.")
        return phone

    # --- GARANTIR QUE USERNAME SEJA O E-MAIL ---
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email # Copia o email para o username
        if commit:
            user.save()
        return user

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu Nome'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Seu E-mail'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Assunto'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Sua Mensagem', 'rows': 4}),
        }

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['street', 'number', 'neighborhood', 'city', 'state', 'zip_code']
        widgets = {
            'street': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rua'}),
            'number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número'}),
            'neighborhood': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bairro'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cidade'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Estado (UF)'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CEP'}),
        }

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(XX) 9XXXX-XXXX'}),
        }