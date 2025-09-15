# dhealth/consumers.py
import json
import django
django.setup()
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import ChatMessage, Booking, Profile
from .encryption import encrypt_message, decrypt_message 
from django.conf import settings
import os

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.bid = self.scope['url_route']['kwargs']['bid']
        self.room_name = f'chat_{self.bid}'
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        raw_msg = data.get('message', '')
        file_url = data.get('file_url')
        file_label = data.get('file_label', '') 
        sender = self.scope['user']
        if isinstance(sender, AnonymousUser):
            return

        booking = await self.get_booking(self.bid)
        profile = await self.get_user_profile(sender)

        enc = encrypt_message(raw_msg) if raw_msg else ''
        msg_obj = await self.create_chat_message(booking, profile, enc, file_url, file_label)

        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'chat_message',
                'sender': sender.username,
                'message': raw_msg,
                'file_url': file_url,
                'file_label': file_label,
                'mid': msg_obj.id,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'sender': event['sender'],
            'message': event.get('message'),
            'file_url': event.get('file_url'),
            'file_label': event.get('file_label'),
            'mid': event.get('mid'),
        }))

    @database_sync_to_async
    def get_booking(self, bid):
        return Booking.objects.get(id=bid)

    @database_sync_to_async
    def get_user_profile(self, user):
        return user.profile

    @database_sync_to_async
    def create_chat_message(self, booking, sender_profile, enc_message, file_url, file_label):
        
        file_path = None
        if file_url:
            
            if file_url.startswith(settings.MEDIA_URL):
                file_path = file_url[len(settings.MEDIA_URL):]  
            else:
                
                file_path = os.path.basename(file_url)
        
        return ChatMessage.objects.create(
            booking=booking,
            sender=sender_profile,
            message=enc_message or '',   
            file=file_path, 
            file_label=file_label or ''
        )