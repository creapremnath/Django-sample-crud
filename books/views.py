import json
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Book

# Authentication
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        confirm = request.POST.get('confirm_password', '').strip()

        if not username or not password:
            messages.error(request, 'Username and password are required.')
        elif password != confirm:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            return redirect('book_list')

    return render(request, 'auth/register.html')


@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        # Handle JSON requests (from React)
        content_type = request.content_type or ''
        if 'application/json' in content_type:
            try:
                data = json.loads(request.body)
                username = data.get('username', '').strip()
                password = data.get('password', '').strip()
            except json.JSONDecodeError:
                return JsonResponse({'detail': 'Invalid JSON'}, status=400)
        else:
            # Handle form requests (from Django templates)
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '').strip()
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if 'application/json' in content_type:
                return JsonResponse({'success': True, 'message': 'Login successful'})
            return redirect('book_list')
        
        if 'application/json' in content_type:
            return JsonResponse({'detail': 'Invalid credentials'}, status=401)
        messages.error(request, 'Invalid credentials, try again.')
    
    return render(request, 'auth/login.html')


@csrf_exempt
def logout_view(request):
    logout(request)
    if request.content_type and 'application/json' in request.content_type:
        return JsonResponse({'success': True, 'message': 'Logout successful'})
    return redirect('login')

# Helpers for API
def _require_auth(request):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'Authentication required'}, status=401)
    return None


def _book_to_dict(book):
    return {
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'description': book.description,
    }


# JSON API (no DRF)
@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_books(request):
    if request.method == "GET":
        auth_error = _require_auth(request)
        if auth_error:
            return auth_error
        books = Book.objects.all()
        return JsonResponse([_book_to_dict(b) for b in books], safe=False)

    # POST create
    auth_error = _require_auth(request)
    if auth_error:
        return auth_error
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'Invalid JSON'}, status=400)

    title = payload.get('title', '').strip()
    author = payload.get('author', '').strip()
    description = payload.get('description', '').strip()
    if not title or not author:
        return JsonResponse({'detail': 'Title and author are required'}, status=400)
    book = Book.objects.create(title=title, author=author, description=description)
    return JsonResponse(_book_to_dict(book), status=201)


@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def api_book_detail(request, id):
    auth_error = _require_auth(request)
    if auth_error:
        return auth_error

    book = get_object_or_404(Book, id=id)

    if request.method == "GET":
        return JsonResponse(_book_to_dict(book))

    if request.method in ["PUT", "PATCH"]:
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON'}, status=400)
        if 'title' in payload:
            book.title = payload['title'].strip()
        if 'author' in payload:
            book.author = payload['author'].strip()
        if 'description' in payload:
            book.description = payload['description']
        if not book.title or not book.author:
            return JsonResponse({'detail': 'Title and author are required'}, status=400)
        book.save()
        return JsonResponse(_book_to_dict(book))

    if request.method == "DELETE":
        book.delete()
        return JsonResponse({'detail': 'Deleted'})

    return HttpResponseNotAllowed(["GET", "PUT", "PATCH", "DELETE"])


# READ (list)
@login_required
def book_list(request):
    books = Book.objects.all()
    return render(request, 'books/book_list.html', {'books': books})

@login_required
def book_create(request):
    if request.method == 'POST':
        title = request.POST['title']
        author = request.POST['author']
        description = request.POST['description']

        Book.objects.create(title=title, author=author, description=description)
        return redirect('book_list')

    return render(request, 'books/book_form.html')

@login_required
def book_update(request, id):
    book = get_object_or_404(Book, id=id)

    if request.method == 'POST':
        book.title = request.POST['title']
        book.author = request.POST['author']
        book.description = request.POST['description']
        book.save()
        return redirect('book_list')

    return render(request, 'books/book_form.html', {'book': book})

@login_required
def book_delete(request, id):
    book = get_object_or_404(Book, id=id)
    book.delete()
    return redirect('book_list')
