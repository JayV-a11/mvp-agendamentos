from starlette.responses import JSONResponse

MAX_PHOTO = 5 * 1024 * 1024


class RequestLimitsMiddleware:
    """Limita também corpos chunked antes de parsear JSON ou decodificar fotos."""
    def __init__(self, app, production=False):
        self.app = app
        self.production = production

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        path = scope['path']

        async def secure_send(message):
            if message['type'] == 'http.response.start':
                headers = list(message.get('headers', []))
                headers += [(b'x-content-type-options', b'nosniff'),
                    (b'x-frame-options', b'DENY'), (b'referrer-policy', b'no-referrer')]
                if path.startswith(('/admin', '/auth')) or path == '/publico/agendamentos':
                    headers.append((b'cache-control', b'no-store'))
                if self.production:
                    headers.append((b'strict-transport-security', b'max-age=31536000'))
                message = {**message, 'headers': headers}
            await send(message)

        if scope['method'] not in {'POST', 'PUT', 'PATCH'}:
            return await self.app(scope, receive, secure_send)
        limit = MAX_PHOTO if path.endswith('/foto') else 64 * 1024
        chunks = []
        size = 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            chunk = message.get('body', b'')
            size += len(chunk)
            if size > limit:
                return await JSONResponse({'detail': 'Arquivo ou requisição excede o tamanho permitido.'}, 413)(
                    scope, receive, secure_send)
            chunks.append(chunk)
            if not message.get('more_body', False):
                break
        body = b''.join(chunks)
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {'type': 'http.request', 'body': body, 'more_body': False}
            return await receive()
        await self.app(scope, replay, secure_send)
