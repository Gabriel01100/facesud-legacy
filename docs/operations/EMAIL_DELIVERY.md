# Entrega de correo electrónico

## Desarrollo local

Compose ejecuta Mailpit como servidor SMTP de captura. El backend envía por SMTP a `mailpit:1025`; Mailpit no entrega mensajes a buzones reales. La interfaz queda disponible en `http://localhost:8025` y se enlaza solo a loopback.

No configurar Mailpit en staging ni producción. No publicar el puerto SMTP ni la interfaz de Mailpit en redes públicas.

## Producción

El backend utiliza SMTP estándar para mantener el proveedor desacoplado. La configuración de producción exige:
- Host y puerto SMTP.
- Usuario y contraseña/API key.
- STARTTLS habilitado.
- Dirección remitente.
- URL HTTPS del frontend y origen CORS HTTPS.

### Proveedor inicial recomendado: Resend

Resend ofrece SMTP compatible con el transporte actual:
- Host: `smtp.resend.com`
- Puerto: `587` (STARTTLS)
- Usuario: `resend`
- Contraseña: API key de Resend.
- Remitente: dirección de un dominio verificado en Resend.

Pasos operativos:
1. Registrar una cuenta en Resend.
2. Agregar un dominio que controles (idealmente un subdominio dedicado a correo transaccional).
3. Publicar los registros DNS que Resend indique para SPF y DKIM; configurar DMARC según la política del dominio.
4. Esperar a que Resend marque el dominio como verificado.
5. Crear una API key con permiso de envío y restringida al dominio emisor cuando sea posible.
6. Configurar las variables del backend mediante el gestor de secretos del entorno:

```env
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USERNAME=resend
SMTP_PASSWORD=<API_KEY>
SMTP_STARTTLS=true
EMAIL_FROM=FaceSud <no-reply@correo.tu-dominio>
FRONTEND_BASE_URL=https://tu-dominio
CORS_ORIGINS=https://tu-dominio
```

No guardar la API key en Git, imágenes Docker, archivos frontend ni logs. No usar el dominio de ejemplo ni un remitente no verificado. Los límites de envío y la política de cuenta deben comprobarse en el panel del proveedor antes de habilitar registros públicos.

## Mensajes enviados

El módulo Identity utiliza el mismo transporte para:
- Verificación de correo (enlace de un solo uso, TTL de 24 horas).
- Recuperación de contraseña (enlace de un solo uso, TTL de 30 minutos).

El envío falla de forma cerrada: si el proveedor no está configurado o rechaza el mensaje, el registro no se confirma como una cuenta pendiente sin correo de verificación enviado. La API no debe revelar tokens en respuestas ni logs.

## Operación posterior

Antes de abrir registros públicos:
- Probar entrega real a Gmail, Outlook y al menos otro proveedor.
- Confirmar SPF, DKIM y DMARC.
- Revisar rebotes, quejas, límites, reputación y métricas.
- Definir alertas y proceso de rotación/revocación de API keys.
- Verificar que el enlace generado usa el dominio HTTPS de producción.
