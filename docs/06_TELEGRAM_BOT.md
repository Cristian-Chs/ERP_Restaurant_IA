# 06. Integración del Bot de Telegram

## Resumen

El bot de Telegram actúa como una interfaz secundaria para el restaurante, permitiendo a los usuarios ordenar sin descargar una app. También sirve como el sistema principal de notificaciones para actualizaciones de pedidos.

## Arquitectura

- **Polling/Webhook**: El bot escucha actualizaciones desde Telegram.
- **Máquina de Estados**: La lógica del bot tiene estado, almacenado en la base de datos (`TelegramSession`). Esto asegura que si el servidor se reinicia, el estado de la conversación del usuario (ej: "Seleccionando Sabor de Pizza") se conserva.

## Flujo de Conversación (Máquina de Estados)

1.  **IDLE**: Estado por defecto. El usuario envía `/start`.
2.  **MENU_VIEW**: El bot envía el menú (o link a WebApp).
3.  **SELECTING_PRODUCT**: El usuario clica un producto.
4.  **SELECTING_QUANTITY**: El bot pregunta "¿Cuántos?".
5.  **CONFIRMING_ORDER**: Se muestra el resumen. El usuario confirma.
6.  **PAYMENT_UPLOAD**: El bot pide una captura/foto del pago.
7.  **WAITING_APPROVAL**: El admin verifica el pago.

## Comandos

| Comando     | Descripción                                           |
| ----------- | ----------------------------------------------------- |
| `/start`    | Inicializa el bot y muestra el mensaje de bienvenida. |
| `/menu`     | Muestra el menú de comida.                            |
| `/soporte`  | Muestra información de contacto.                      |
| `/myorders` | Muestra historial de pedidos (si está implementado).  |

## Puntos de Integración

- **Notificaciones**: Cuando el Panel de Cocina marca un pedido como "Listo", el backend dispara una función específica del bot para enviar un mensaje al `telegram_id` asociado a ese pedido.
- **WebApp**: El bot usa Telegram Mini Apps (WebApps) para embeber el Menú React para una experiencia más rica.
