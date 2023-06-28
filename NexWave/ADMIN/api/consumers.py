from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Add the user to the WebSocket group
        await self.channel_layer.group_add("admin", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Remove the user from the WebSocket group
        await self.channel_layer.group_discard("admin", self.channel_name)

    async def receive(self, text_data):
        # Handle incoming WebSocket messages
        pass  # Add your custom logic here

    async def notification(self, event):
        # Handle notification events
        message = event['message']
        await self.send(text_data=message)
