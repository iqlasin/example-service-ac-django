from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Sum, functions
from django.db.models.functions import ExtractMonth
from django.utils.dateparse import parse_datetime
from datetime import datetime

from .models import Service, User, Harga, Teknisi
from .forms import RegisterForm, UserForm

import json



def index(request):
    return render(request, 'service_ac/index.html')

def logout_view(request):
    request.session.flush()
    return redirect('home')

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            user = User.objects.get(username=form.cleaned_data['username'])
            # request.session['username'] = form.cleaned_data['username']
            # request.session['role'] = 'user'
            request.session['username'] = user.username
            request.session['role'] = user.role
            request.session['user_id'] = user.id
            return redirect('user_dashboard') 
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegisterForm()

    return render(request, 'service_ac/auth/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        try:
            user = User.objects.get(username=username)
            
            if check_password(password, user.password):
                request.session['username'] = user.username
                request.session['role'] = user.role
                request.session['user_id'] = user.id
                
                if user.role == 'admin':
                    return redirect('admin_dashboard')
                elif user.role == 'teknisi':
                    return redirect('teknisi_dashboard')
                else:
                    return redirect('user_dashboard')
            else:
                messages.error(request, 'Invalid username or password')
        except User.DoesNotExist:
            messages.error(request, 'Invalid username or password')

    return render(request, 'service_ac/auth/login.html')

def admin_dashboard(request):
    if request.session.get('role') != 'admin':
        return redirect('login')

    order_data = list(
        Service.objects
        .annotate(month=functions.ExtractMonth('tanggal_servis'))
        .values('month')
        .annotate(order_count=Count('id'))
        .order_by('month')
    )

    total_pendapatan = Service.objects.filter(status='selesai').aggregate(Sum('harga'))['harga__sum'] or 0

    context = {
        "username": request.user.username,
        "order_data": order_data,
        "total_pendapatan": total_pendapatan,
    }

    return render(request, 'service_ac/admin/admin_dashboard.html', context)


def teknisi_dashboard(request):
    if request.session.get('role') not in ['teknisi', 'admin']:
        return redirect('login')
    
    teknisi = Teknisi.objects.get(nama=request.session.get('username'))
    
    jobs = Service.objects.filter(teknisi=teknisi)

    monthly_stats = (
        Service.objects.filter(teknisi=teknisi)
        .values('tanggal_servis__month')
        .annotate(count=Count('id'))
        .order_by('tanggal_servis__month')
    )

    stats_data = []
    for stat in monthly_stats:
        stats_data.append({
            'month': stat['tanggal_servis__month'],
            'count': stat['count']
        })

    return render(
        request,
        'service_ac/teknisi/teknisi_dashboard.html',
        {
            'jobs': jobs,
            'monthly_stats': json.dumps(stats_data),
            'username': request.session.get('username'),
        }
    )


def history_service(request):
    if request.session.get('role') != 'admin':
        return redirect('login') 

    history_services = Service.objects.order_by('-tanggal_servis')
    
    context = {
        'services': history_services
    }
    return render(request, 'service_ac/admin/history_service.html', context)


def user_dashboard(request):
    if request.session.get('role') not in ['user', 'admin']:
        return redirect('login') 

    user_id = request.session.get('user_id') 

    order_data = (
        Service.objects.filter(user_id=user_id) 
        .annotate(month=ExtractMonth('tanggal_servis'))
        .values('month') 
        .annotate(order_count=Count('id'))
        .order_by('month')
    )

    order_data_list = [
        {'month': item['month'], 'order_count': item['order_count']}
        for item in order_data
    ]

    return render(request, 'service_ac/user/user_dashboard.html', {
        'order_data': order_data_list
    })



def order_service(request):
    if request.session.get('role') != 'user' and request.session.get('role') != 'admin':
        return redirect('login') 

    harga_obj = Harga.objects.first()
    if not harga_obj:
        messages.error(request, 'Harga tidak tersedia.')
        return redirect('order_service')
    harga = harga_obj.service_ac

    if request.method == 'POST':
        tanggal_servis = request.POST['tanggal_servis']
        deskripsi = request.POST['deskripsi']
        location = request.POST['location']
        user_id = request.session.get('user_id') 

        try:
            tanggal_servis = parse_datetime(tanggal_servis)  # parse_datetime ke DateTime
            if not tanggal_servis:
                raise ValueError("Format tanggal tidak valid.")
        except ValueError:
            messages.error(request, 'Format tanggal tidak valid.')
            return redirect('order_service')
        service = Service(
            user_id=user_id, 
            teknisi_id=None, 
            tanggal_servis=tanggal_servis,
            harga=harga,
            status='menunggu',
            deskripsi=deskripsi,
            location=location
        )
        service.save()
        return render(request, 'service_ac/user/order_service.html', {'harga': harga, 'success': 'Service berhasil dipesan!'})

    return render(request, 'service_ac/user/order_service.html', {'harga': harga})


def profile(request):
    if request.session.get('role') not in ['user', 'admin']:
        return redirect('login')

    user_id = request.session.get('user_id')
    user = get_object_or_404(User, id=user_id)

    message = None
    message_type = None

    if request.method == 'POST' and 'update_info' in request.POST:
        alamat = request.POST['alamat']
        nomor_hp = request.POST['nomor_hp']

        user.alamat = alamat
        user.nomor_hp = nomor_hp
        user.save()

        message = "Information updated successfully."
        message_type = "success"

    if request.method == 'POST' and 'change_password' in request.POST:
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        # Validate old password
        if check_password(old_password, user.password):
            # Validate new password confirmation
            if new_password == confirm_password:
                user.password = make_password(new_password)
                user.save()

                message = "Password updated successfully."
                message_type = "success"
                # return redirect('login') 
            else:
                message = "New passwords do not match."
                message_type = "error"
        else:
            message = "Old password is incorrect."
            message_type = "error"

    return render(request, 'service_ac/user/profile.html', {
        'user': user,
        'message': message,
        'message_type': message_type,
    })


def view_orders(request):
    if request.session.get('role') != 'user' and request.session.get('role') != 'admin':
        return redirect('login')
    orders = Service.objects.filter(user_id=request.session.get('user_id'))
    return render(request, 'service_ac/user/view_orders.html', {'orders': orders})

def manage_service(request):
    if request.session.get('role') != 'admin':
        return redirect('login')

    services = Service.objects.filter(teknisi=None)
    teknisis = Teknisi.objects.all()

    return render(request, 'service_ac/admin/manage_service.html', {'services': services, 'teknisis': teknisis})

@csrf_exempt
def api_manage_service(request):
    response = {'success': False}

    if request.method == 'POST':
        service_id = request.POST.get('service_id')
        teknisi_id = request.POST.get('teknisi_id')

        try:
            service = Service.objects.get(id=service_id)
            teknisi = Teknisi.objects.get(id=teknisi_id)
            service.teknisi = teknisi
            service.save()
            response['success'] = True
            response['message'] = 'Technician assigned successfully'
        except Service.DoesNotExist or Teknisi.DoesNotExist:
            response['message'] = 'Service or Technician not found'

    return JsonResponse(response)

@csrf_exempt
def api_manage_harga(request):
    if request.session.get('role') != 'admin':
        return redirect('login')

    if request.method == 'POST':
        try:
            service_ac = request.POST.get('service_ac')

            if service_ac is None or not service_ac.strip():
                return JsonResponse({'success': False, 'error': 'Field "service_ac" harus diisi.'}, status=400)
            
            harga, created = Harga.objects.get_or_create(id=1) 
            harga.service_ac = service_ac
            harga.save()

            message = 'Harga baru dibuat.' if created else 'Harga berhasil diperbarui.'
            return JsonResponse({'success': True, 'message': message, 'data': {'id': harga.id, 'service_ac': harga.service_ac}})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    elif request.method == 'GET': 
        try:
            harga = Harga.objects.first()
            if harga:
                return JsonResponse({'success': True, 'data': {'id': harga.id, 'service_ac': harga.service_ac}})
            return JsonResponse({'success': True, 'data': None, 'message': 'Belum ada data harga.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Method not allowed.'}, status=405)

def manage_harga(request):
    if request.session.get('role') != 'admin':
        return redirect('login')
    return render(request, 'service_ac/admin/manage_harga.html')


@csrf_exempt
def api_manage_teknisi(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        teknisi_id = data.get('id')
        nama = data.get('nama')
        alamat = data.get('alamat')
        nomor_hp = data.get('nomor_hp')
        spesialisasi = data.get('spesialisasi')
        password = data.get('password')

        if teknisi_id:
            teknisi = get_object_or_404(Teknisi, nama=nama)
            teknisi.nama = nama
            teknisi.alamat = alamat
            teknisi.nomor_hp = nomor_hp
            teknisi.spesialisasi = spesialisasi
            teknisi.save()

            user = get_object_or_404(User, username=teknisi.nama)
            user.username = nama
            if password:
                user.password = make_password(password)
            user.alamat = alamat
            user.nomor_hp = nomor_hp
            user.save()
        else:
            teknisi = Teknisi.objects.create(
                nama=nama,
                alamat=alamat,
                nomor_hp=nomor_hp,
                spesialisasi=spesialisasi,
            )
            User.objects.create(
                username=nama,
                password=make_password(password),
                role='teknisi',
                alamat=alamat,
                nomor_hp=nomor_hp,
            )
        return JsonResponse({'success': True, 'message': 'Technician saved successfully'})

    elif request.method == 'DELETE':
        data = json.loads(request.body)
        nama = data.get('nama')  # Ambil nama teknisi dari body
        if nama:
            try:
                teknisi = Teknisi.objects.get(nama=nama)
                teknisi.delete()

                # Hapus user terkait
                User.objects.filter(username=nama).delete()

                return JsonResponse({'success': True, 'message': 'Technician deleted successfully'})
            except Teknisi.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Technician not found'}, status=404)
        else:
            return JsonResponse({'success': False, 'message': 'Nama teknisi is required for deletion'}, status=400)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)

def manage_teknisi(request):
    if request.session.get('role') != 'admin':
        return redirect('login')  # Redirect jika bukan admin

    teknisi_list = Teknisi.objects.all()
    context = {
        'teknisi_list': teknisi_list,
    }
    return render(request, 'service_ac/admin/manage_teknisi.html', context)


def manage_users(request):
    if request.session.get('role') != 'admin':
        return redirect('login')
    # users = User.objects.all() 
    users = list(User.objects.filter(role="user").values())
    return render(request, 'service_ac/admin/manage_users.html', {'users': users})

@csrf_exempt
def user_list(request):
    if request.session.get('role') != 'admin':
        return redirect('login')
    if request.method == 'GET':
        # users = list(User.objects.values())
        users = list(User.objects.filter(role="user").values())
        return JsonResponse(users, safe=False)
    elif request.method == 'POST':
        data = json.loads(request.body)
        user = User.objects.create(
            username=data['username'],
            role=data['role'],
            alamat=data['alamat'],
            nomor_hp=data['nomor_hp']
        )
        if data.get('password'):
            user.password = make_password(data['password'])
            user.save()
        return JsonResponse({'id': user.id})

@csrf_exempt
def user_detail(request, user_id):
    if request.session.get('role') != 'admin':
        return redirect('login')
    user = get_object_or_404(User, id=user_id)
    if request.method == 'GET':
        return JsonResponse({
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'alamat': user.alamat,
            'nomor_hp': user.nomor_hp
        })
    elif request.method == 'PUT':
        data = json.loads(request.body)
        user.username = data['username']
        user.role = data['role']
        user.alamat = data['alamat']
        user.nomor_hp = data['nomor_hp']

        if data.get('password'):
            user.password = make_password(data['password'])  # Hash password

        user.save()
        return JsonResponse({'success': True})
    elif request.method == 'DELETE':
        user.delete()
        return JsonResponse({'success': True})

def manage_jobs(request):
    if request.session.get('role') != 'teknisi':
        return redirect('login')
    teknisi = Teknisi.objects.get(nama=request.session.get('username'))
    jobs = Service.objects.filter(teknisi=teknisi)
    status_message = None
    if request.method == 'POST':
        job_id = request.POST.get('job_id')
        status = request.POST.get('status')
        if status not in ['menunggu', 'dikerjakan', 'selesai']:
            status_message = 'Status tidak valid.'
        else:
            try:
                job = Service.objects.get(id=job_id, teknisi=teknisi)
                job.status = status
                job.save()
                status_message = 'Status pekerjaan berhasil diubah.'
            except Service.DoesNotExist:
                status_message = 'Pekerjaan tidak ditemukan.'

    return render(request, 'service_ac/teknisi/manage_jobs.html', {
        'jobs': jobs,
        'status_message': status_message,
    })


def update_status(request, job_id):
    if request.session.get('role') != 'teknisi':
        return JsonResponse({"error": "Unauthorized"}, status=403)
    
    if request.method == 'POST':
        try:
            job = Service.objects.get(id=job_id, teknisi__nama=request.session.get('username'))
            status = request.POST.get('status')
            if status not in ['menunggu', 'dikerjakan', 'selesai']:
                return JsonResponse({"error": "Invalid status"}, status=400)
            job.status = status
            job.save()
            return JsonResponse({"message": "Status updated successfully"})
        
        except Service.DoesNotExist:
            return JsonResponse({"error": "Job not found"}, status=404)
    else:
        return JsonResponse({"error": "Invalid method"}, status=405)


# Not safe
def create_admin(request):
    if not User.objects.filter(username='admin').exists():
        username = 'admin'
        password = make_password('admin')  # Hash password
        role = 'admin'
        alamat = 'admin'
        nomor_hp = 'admin'
        user = User(username=username, password=password, role=role, alamat=alamat, nomor_hp=nomor_hp)
        user.save()
        return render(request, 'service_ac/auth/success.html', {'message': 'Admin user inserted successfully.'})
    else:
        return render(request, 'service_ac/auth/success.html', {'message': 'Admin user already exists.'})
    