from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException

def custom_exception_handler(exc, context):
    """
    Manejador de excepciones personalizado para DRF.
    Formatea las respuestas de error en un formato JSON consistente.
    """
    # Primero, obtenemos la respuesta de error estándar de DRF
    response = exception_handler(exc, context)

    # Si DRF manejó la excepción, reformateamos la respuesta
    if response is not None:
        # Mapeo de códigos de estado a códigos de error personalizados
        error_map = {
            status.HTTP_404_NOT_FOUND: "not_found",
            status.HTTP_403_FORBIDDEN: "permission_denied",
            status.HTTP_401_UNAUTHORIZED: "unauthenticated",
            status.HTTP_400_BAD_REQUEST: "bad_request",
            status.HTTP_429_TOO_MANY_REQUESTS: "throttled",
        }
        
        error_code = error_map.get(response.status_code, "server_error")
        
        details = None
        message = ""

        if isinstance(response.data, dict):
            # Para errores de validación, el detalle es un diccionario
            if 'detail' in response.data:
                message = str(response.data['detail'])
            else:
                # Tomamos el primer mensaje de error del primer campo
                first_key = next(iter(response.data))
                first_error = response.data[first_key][0]
                message = f"{first_key}: {first_error}"
                details = response.data
        elif isinstance(response.data, list):
            message = str(response.data[0])
        
        # Construimos nuestra respuesta personalizada
        custom_response_data = {
            'success': False,
            'error_code': error_code,
            'message': message,
            'details': details
        }
        
        # Reemplazamos los datos de la respuesta original con nuestro formato
        response.data = custom_response_data
    # Si es una excepción no manejada por DRF pero es de DRF, la formateamos también
    elif isinstance(exc, APIException):
        custom_response_data = {
            'success': False,
            'error_code': exc.default_code,
            'message': exc.detail,
            'details': None
        }
        response = Response(custom_response_data, status=exc.status_code)

    return response
