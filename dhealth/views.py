from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .forms import UserForm, DocForm, PatForm, SlotForm
from .models import Profile, Slot, Booking, ChatMessage
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.files.storage import default_storage
import os
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .encryption import encrypt_message, decrypt_message
from django.utils import timezone
from django.utils.timezone import now
from datetime import date
from django.db import models

def home(request):
    return render(request, 'home.html')

def reg_doc(request):
    if request.method == 'POST':
        uf = UserForm(request.POST)
        df = DocForm(request.POST, request.FILES)
        if uf.is_valid() and df.is_valid():
            u = uf.save(commit=False)
            u.set_password(u.password)
            u.save()
            p = df.save(commit=False)
            p.user = u
            p.is_doc = True
            p.save()
            return redirect('wait')
    else:
        uf = UserForm()
        df = DocForm()
    return render(request, 'reg_doc.html', {'uf': uf, 'df': df})

def reg_pat(request):
    if request.method == 'POST':
        uf = UserForm(request.POST)
        pf = PatForm(request.POST)
        if uf.is_valid() and pf.is_valid():
            u = uf.save(commit=False)
            u.set_password(u.password)
            u.save()
            p = pf.save(commit=False)
            p.user = u
            p.save()
            return redirect('wait')
    else:
        uf = UserForm()
        pf = PatForm()
    return render(request, 'reg_pat.html', {'uf': uf, 'pf': pf})

def wait(request):
    return render(request, 'wait.html')

def log_out(request):
    is_admin = request.session.get('adm')
    logout(request)
    request.session.flush()
    if is_admin:
        return redirect('adlog')  
    return redirect('logn')       


def logn(request):
    if request.method == 'POST':
        un = request.POST.get('username')
        pw = request.POST.get('password')
        u = authenticate(request, username=un, password=pw)
        if u:
            p = Profile.objects.get(user=u)
            if p.is_active:
                login(request, u)
                return redirect('dash')
            else:
                return redirect('wait')
        else:
            messages.error(request, 'invalid')
    return render(request, 'login.html')

@login_required(login_url=reverse_lazy('logn'))
def dash(request):
    try:
        p = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        return redirect('logn')

    if not p.is_active:
        return render(request, 'wait.html')  # waiting for admin approval

    if p.is_doc:
        return redirect('docdash')
    else:
        return redirect('patdash')


def adlog(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        if u == settings.ADMIN_USER and p == settings.ADMIN_PASS:
            request.session['adm'] = True
            return redirect('adpanel')
    return render(request, 'admin_login.html')

def adpanel(request):
    if not request.session.get('adm'):
        return redirect('adlog')
    d = Profile.objects.filter(is_doc=True)
    p = Profile.objects.filter(is_doc=False)
    return render(request, 'admin_panel.html', {'d': d, 'p': p})

def toggleuser(request, pid):
    if not request.session.get('adm'):
        return redirect('adlog')
    x = Profile.objects.get(id=pid)
    x.is_active = not x.is_active
    x.user.is_active = x.is_active  
    x.user.save()
    x.save()

    if x.is_active:
        subject = "Your account has been approved"
        message = f"Hello {x.user.first_name},\n\nYour account on the Digital Healthcare system has been approved. You can now log in and start using the services.\n\nThank you!"
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [x.user.email], fail_silently=True)

    return redirect('adpanel')

@login_required(login_url=reverse_lazy('logn'))
def docdash(request):
    prof = get_object_or_404(Profile, user=request.user, is_doc=True)

    if request.method == "POST":
        form = SlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.doc = prof
            if slot.date < date.today():
                messages.error(request, "Cannot create slot for a past date.")
            elif Slot.objects.filter(doc=prof, date=slot.date, time=slot.time).exclude(
                id__in=Booking.objects.filter(status='cancelled').values_list('slot_id', flat=True)
                ).exists():
                messages.error(request, "This slot already exists.")

            else:
                slot.save()
                messages.success(request, "Slot created successfully.")
                return redirect('docdash')
    else:
        form = SlotForm()

    show_all = request.GET.get("show") == "all"
    show_bookings_all = request.GET.get("show_bookings") == "all"

    cancelled_slot_ids = Booking.objects.filter(status='cancelled').values_list('slot_id', flat=True)
    all_slots = Slot.objects.filter(doc=prof).exclude(id__in=cancelled_slot_ids).order_by("-date", "-time")
    upcoming_slots = all_slots.filter(date__gte=date.today())
    past_slots = all_slots.filter(date__lt=date.today())

    all_bookings = Booking.objects.filter(doc=prof).order_by("-slot__date", "-slot__time")
    upcoming_bookings = all_bookings.filter(slot__date__gte=date.today())
    past_bookings = all_bookings.filter(slot__date__lt=date.today())

    return render(request, 'docdash.html', {
        'f': form,
        's': upcoming_slots if not show_all else past_slots,
        'show_all': show_all,
        'b': upcoming_bookings if not show_bookings_all else past_bookings,
        'show_bookings_all': show_bookings_all,
        'today': date.today(),
    })

def delete_user(request, pid):
  
    if not request.session.get('adm'):
        return redirect('adlog')
    
    profile = get_object_or_404(Profile, id=pid)
    user = profile.user
    username = user.first_name or user.username  
    
    
    user.delete()
    
    
    request.session['adm'] = True
    
    messages.success(request, f"User {username} has been successfully deleted.")
    return redirect('adpanel')

@login_required(login_url=reverse_lazy('logn'))
def chat_view(request, bid):
    p = get_object_or_404(Profile, user=request.user)
    b = get_object_or_404(Booking, id=bid)

    if p != b.doc and p != b.pat:
        return render(request, 'denied.html')

    if request.method == 'POST':
        txt = request.POST.get('msg')
        if txt:
            ChatMessage.objects.create(
                booking=b,
                sender=p,
                message=encrypt_message(txt)
            )
            return redirect('chat', bid=bid)

    msgs = ChatMessage.objects.filter(booking=b).order_by('sent_at')
    for m in msgs:
       
        try:
            m.message = decrypt_message(m.message)
        except Exception:
            m.message = "[Unable to decrypt message]"

    return render(request, 'chat.html', {'b': b, 'msgs': msgs})

@csrf_exempt
def cancel_booking(request, bid):
    if request.method == "POST":
        try:
            booking = Booking.objects.get(id=bid)
            booking.status = 'cancelled'
            booking.save()
            messages.success(request, "Appointment has been successfully cancelled.")
        except Booking.DoesNotExist:
            messages.error(request, "Booking not found or already cancelled.")
        return redirect('docdash')

@csrf_exempt
def cancel_booking_patient(request, bid):
    if request.method == "POST":
        try:
            booking = Booking.objects.get(id=bid, pat__user=request.user)
            booking.status = 'cancelled'
            booking.save()
            messages.success(request, "Your appointment has been successfully cancelled.")
        except Booking.DoesNotExist:
            messages.error(request, "Booking not found or already cancelled.")
    return redirect('patdash')


# @login_required(login_url=reverse_lazy('adlog'))
def adminstats(request):
    from django.db.models import Count

    total_doctors = Profile.objects.filter(is_doc=True).count()
    total_patients = Profile.objects.filter(is_doc=False).count()
    total_bookings = Booking.objects.count()
    cancelled = Booking.objects.filter(status='cancelled').count()
    confirmed = Booking.objects.filter(status='confirmed').count()

    most_active_doc = Profile.objects.filter(is_doc=True).annotate(
        appt_count=Count('d')
    ).order_by('-appt_count').first()

    return render(request, 'admin_stats.html', {
        'total_doctors': total_doctors,
        'total_patients': total_patients,
        'total_bookings': total_bookings,
        'cancelled': cancelled,
        'confirmed': confirmed,
        'most_active_doc': most_active_doc,
    })

def appointment_logs(request):
    all_bookings = Booking.objects.all().order_by('-created')
    return render(request, 'admin_appointment_logs.html', {'bookings': all_bookings})

@login_required(login_url=reverse_lazy('logn'))
def reschedule_booking(request, bid):
    try:
        profile = request.user.profile
        if profile.is_doc:
            b = get_object_or_404(Booking, id=bid, doc=profile)
        else:
            b = get_object_or_404(Booking, id=bid, pat=profile)
    except:
        b = get_object_or_404(Booking, id=bid, pat__user=request.user)
    
    used_slot_ids = Booking.objects.exclude(id=b.id).values_list('slot_id', flat=True)
    now = timezone.now()
    current_date = now.date()
    current_time = now.time()
    
    available_slots = Slot.objects.filter(
        doc=b.doc
    ).filter(
        models.Q(date__gt=current_date) |
        models.Q(date=current_date, time__gt=current_time)
    ).exclude(
        id__in=used_slot_ids
    ).exclude(
        id=b.slot.id
    )
    
    if request.method == "POST":
        new_slot_id = request.POST.get('new_slot')
        
        if not new_slot_id:
            messages.error(request, "Please select a slot.")
            return redirect('reschedule_booking', bid=b.id)
            
        try:
            new_slot = Slot.objects.get(id=new_slot_id, doc=b.doc)
            
            if Booking.objects.filter(slot=new_slot).exclude(id=b.id).exists():
                messages.error(request, "Selected slot is already booked.")
                return redirect('reschedule_booking', bid=b.id)
        
            b.slot = new_slot
            b.save()
            
            messages.success(request, "Appointment rescheduled successfully.")
            
            if request.user.profile.is_doc:
                return redirect('docdash')  
            else:
                return redirect('patdash')
            
        except Slot.DoesNotExist:
            messages.error(request, "Invalid slot selected.")
            return redirect('reschedule_booking', bid=b.id)

    return render(request, 'reschedule.html', {
        'booking': b,
        'available_slots': available_slots
    })



@login_required(login_url=reverse_lazy('logn'))
def download_chat_file(request, mid):
    m = get_object_or_404(ChatMessage, id=mid)
    user_profile = get_object_or_404(Profile, user=request.user)

   
    if user_profile != m.booking.doc and user_profile != m.booking.pat:
        return render(request, 'denied.html')

    if not m.file:
        raise Http404("No file attached")

    m.file_downloads = (m.file_downloads or 0) + 1
    m.save(update_fields=['file_downloads'])

    response = FileResponse(
        open(m.file.path, 'rb'),
        as_attachment=True,
        filename=smart_str(os.path.basename(m.file.name))
    )
    return response


@csrf_exempt
def upload_chat_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        bid = request.POST.get('bid')
        
        try:
            booking = Booking.objects.get(id=bid)
            
            filename = f"chat_files/{uploaded_file.name}"
            saved_path = default_storage.save(filename, uploaded_file)
            
            
            file_url = f"{settings.MEDIA_URL}{saved_path}"
            
            return JsonResponse({'file_url': file_url, 'filename': saved_path})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid upload'}, status=400)



import os, mimetypes
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.encoding import smart_str
from .models import Profile
from django.views.decorators.http import require_POST

def _ensure_admin(request):
    return bool(request.session.get('adm'))

def _resolve_file(f):
    path = getattr(f, "path", None)
    if not path or not os.path.exists(path):
        raise Http404("File not found.")
    return path

def panel_preview_license(request, pid):
    if not _ensure_admin(request):
        return redirect('adlog')
    prof = get_object_or_404(Profile, id=pid, is_doc=True)
    if not prof.license:
        raise Http404("No file.")
    file_path = _resolve_file(prof.license)
    ext = os.path.splitext(file_path)[1].lower()
    ctype, _ = mimetypes.guess_type(file_path)
    ctype = ctype or "application/octet-stream"
    if ext in (".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp"):
        return FileResponse(open(file_path, "rb"), content_type=ctype)
    return redirect('panel_download_license', pid=pid)

def panel_download_license(request, pid):
    if not _ensure_admin(request):
        return redirect('adlog')
    prof = get_object_or_404(Profile, id=pid, is_doc=True)
    if not prof.license:
        raise Http404("No file.")
    file_path = _resolve_file(prof.license)
    ctype, _ = mimetypes.guess_type(file_path)
    ctype = ctype or "application/octet-stream"
    filename = os.path.basename(prof.license.name)
    return FileResponse(open(file_path, "rb"), content_type=ctype, as_attachment=True, filename=smart_str(filename))


@login_required
@require_POST
def add_feedback(request, bid):
    b = get_object_or_404(Booking, id=bid, pat__user=request.user, status='confirmed')
    rating = int(request.POST.get('rating', 0))
    comment = (request.POST.get('comment') or "").strip()
    if rating not in (1, 2, 3, 4, 5):
        messages.error(request, "Pick a rating from 1 to 5.")
        return redirect('patdash')
    b.feedback_rating = rating
    b.feedback_comment = comment
    b.save()
    messages.success(request, "Thanks for your feedback.")
    return redirect('patdash')




@login_required(login_url=reverse_lazy('logn'))
def patdash(request):
    p = get_object_or_404(Profile, user=request.user)

    if not p.is_active:
        return render(request, 'wait.html')
    if p.is_doc:
        return render(request, 'denied.html')

    docs = Profile.objects.filter(is_doc=True, is_active=True)
    
    
    current_datetime = timezone.now()
    current_date = current_datetime.date()
    current_time = current_datetime.time()
    
    
    slots = Slot.objects.filter(doc__in=docs).exclude(
        id__in=Booking.objects.filter(status='confirmed').values_list('slot_id', flat=True)
    ).filter(
        
        models.Q(date__gt=current_date) | 
        models.Q(date=current_date, time__gt=current_time)
    ).order_by('date', 'time')

    show_all = request.GET.get("show") == "all"
    
    
    all_bookings = Booking.objects.filter(pat=p).order_by('-slot__date', '-slot__time')
    
    
    if show_all:
        
        bookings = all_bookings.filter(
            models.Q(slot__date__lt=current_date) | 
            models.Q(slot__date=current_date, slot__time__lt=current_time)
        )
    else:
      
        bookings = all_bookings.filter(
            models.Q(slot__date__gt=current_date) | 
            models.Q(slot__date=current_date, slot__time__gte=current_time)
        )

    if request.method == 'POST':
        if 'slot' in request.POST:
            sid = request.POST.get('slot')
            try:
                s = Slot.objects.get(id=sid)
                
                
                if (s.date > current_date) or (s.date == current_date and s.time > current_time):
                    if Booking.objects.filter(slot=s, status='confirmed').exists():
                        messages.warning(request, "Sorry, this slot has already been booked.")
                    else:
                        Booking.objects.create(doc=s.doc, pat=p, slot=s)
                        messages.success(request, "Appointment booked successfully!")
                else:
                    messages.error(request, "Cannot book past slots.")
            except Slot.DoesNotExist:
                messages.error(request, "Selected slot does not exist or was already removed.")
            return redirect('patdash')
        
        elif 'feedback_rating' in request.POST:
            bid = request.POST.get('booking_id')
            booking = get_object_or_404(Booking, id=bid, pat=p)
            
            
            appointment_completed = (
                (booking.slot.date < current_date) or 
                (booking.slot.date == current_date and booking.slot.time < current_time)
            )
            
            if appointment_completed and booking.status == 'confirmed':
                rating = request.POST.get('feedback_rating')
                comment = request.POST.get('feedback_comment', '')
                if booking.feedback_rating is None and rating:
                    booking.feedback_rating = int(rating)
                    booking.feedback_comment = comment
                    booking.save()
                    messages.success(request, "Feedback submitted successfully!")
                else:
                    messages.warning(request, "Feedback already submitted for this appointment.")
            else:
                messages.error(request, "Cannot provide feedback for incomplete or cancelled appointments.")
            return redirect('patdash')

    return render(request, 'patdash.html', {
        'slots': slots,
        'b': bookings,
        'show_all': show_all,
        'today': current_date,
        'current_time': current_time,
    })

def doctor_feedback(request, doctor_id):
    if not request.session.get('adm'):
        return redirect('adlog')
    
    doctor = get_object_or_404(Profile, id=doctor_id, is_doc=True)
    
    
    feedback_bookings = Booking.objects.filter(
        doc=doctor,
        feedback_rating__isnull=False,
        status='confirmed'
    ).select_related('pat__user', 'slot').order_by('-created')
    
    
    total_ratings = feedback_bookings.count()
    if total_ratings > 0:
        avg_rating = sum(b.feedback_rating for b in feedback_bookings) / total_ratings
        avg_rating = round(avg_rating, 2)
    else:
        avg_rating = 0
    
    
    rating_counts = {i: 0 for i in range(1, 6)}
    for booking in feedback_bookings:
        rating_counts[booking.feedback_rating] += 1
    
    return render(request, 'doctor_feedback.html', {
        'doctor': doctor,
        'feedback_bookings': feedback_bookings,
        'total_ratings': total_ratings,
        'avg_rating': avg_rating,
        'rating_counts': rating_counts,
    })

def edit_user(request, pid):
   
    if not request.session.get('adm'):
        return redirect('adlog')
    
    profile = get_object_or_404(Profile, id=pid)
    user = profile.user
    
    if request.method == 'POST':
        
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.username = request.POST.get('username', '')
        
        
        if User.objects.filter(username=user.username).exclude(id=user.id).exists():
            messages.error(request, 'Username already exists. Please choose a different username.')
            return render(request, 'edit_user.html', {
                'profile': profile, 
                'user': user,
                'error': 'Username already exists'
            })
        
        
        if User.objects.filter(email=user.email).exclude(id=user.id).exists():
            messages.error(request, 'Email already exists. Please choose a different email.')
            return render(request, 'edit_user.html', {
                'profile': profile, 
                'user': user,
                'error': 'Email already exists'
            })
        
        try:
            user.save()
            
            
            profile.address = request.POST.get('address', '')
            
            if profile.is_doc:
                profile.spec = request.POST.get('spec', '')
                
                if 'license' in request.FILES:
                    profile.license = request.FILES['license']
            
            profile.save()
            
            messages.success(request, f'User {user.first_name} {user.last_name} updated successfully!')
            return redirect('adpanel')
            
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
    
    return render(request, 'edit_user.html', {
        'profile': profile,
        'user': user,
    })