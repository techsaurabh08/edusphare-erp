from channels.generic.websocket import AsyncWebsocketConsumer
import json

class AttendanceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("attendance", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("attendance", self.channel_name)

    async def send_code(self, event):
        await self.send(text_data=json.dumps({
            'code': event['code']
        }))
