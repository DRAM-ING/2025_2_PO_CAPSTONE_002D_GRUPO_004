# location: apps/workorders/presigned_url_view.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
import boto3, os, uuid
from datetime import timedelta
from botocore.exceptions import ClientError

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def presigned_url_view(request):
    """
    Endpoint para subir archivos directamente al backend.
    El backend se encarga de subirlos a S3/LocalStack.
    """
    # Verificar si hay un archivo en la petición
    if 'file' not in request.FILES:
        return Response(
            {"detail": "No se proporcionó archivo"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    file = request.FILES['file']
    ot_id = request.data.get("ot")
    tipo = request.data.get("tipo", "FOTO")
    descripcion = request.data.get("descripcion", "")
    
    # Configurar S3
    bucket = os.getenv("AWS_STORAGE_BUCKET_NAME", "pgf-evidencias-dev")
    s3_endpoint_internal = os.getenv("AWS_S3_ENDPOINT_URL", "http://localstack:4566")
    
    # URL pública para acceder a LocalStack desde el navegador
    # En producción con Cloudflare Tunnel, debe ser la URL del túnel que expone LocalStack
    s3_endpoint_public = os.getenv("AWS_PUBLIC_URL_PREFIX")
    if not s3_endpoint_public:
        cloudflare_url = os.getenv("CLOUDFLARE_TUNNEL_URL", "").rstrip("/")
        if cloudflare_url:
            s3_endpoint_public = f"{cloudflare_url}/localstack"
        else:
            s3_endpoint_public = "http://localhost:4566"
    
    s3 = boto3.client(
        "s3",
        endpoint_url=s3_endpoint_internal,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
        region_name=os.getenv("AWS_S3_REGION_NAME", "us-east-1"),
    )
    
    # Verificar y crear bucket si no existe (solo para LocalStack)
    use_local = s3_endpoint_internal and ("localstack" in s3_endpoint_internal.lower() or "localhost:4566" in s3_endpoint_internal.lower())
    if use_local:
        try:
            s3.head_bucket(Bucket=bucket)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404' or error_code == 'NoSuchBucket':
                # Crear bucket si no existe
                try:
                    s3.create_bucket(Bucket=bucket)
                except Exception as create_error:
                    return Response(
                        {"detail": f"Error al crear bucket: {str(create_error)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
    
    # Generar key único
    key = f"evidencias/ot_{ot_id or 'general'}/{uuid.uuid4()}_{file.name}"
    
    try:
        # Subir archivo a S3
        s3.upload_fileobj(
            file,
            bucket,
            key,
            ExtraArgs={'ContentType': file.content_type or 'application/octet-stream'}
        )
        
        # Generar URL pública
        file_url = f"{s3_endpoint_public}/{bucket}/{key}"
        
        # Crear registro de evidencia
        from apps.workorders.models import Evidencia
        from apps.workorders.models import OrdenTrabajo
        
        ot = None
        if ot_id:
            try:
                ot = OrdenTrabajo.objects.get(id=ot_id)
            except OrdenTrabajo.DoesNotExist:
                pass
        
        evidencia = Evidencia.objects.create(
            ot=ot,
            url=file_url,
            tipo=tipo,
            descripcion=descripcion,
            subido_por=request.user
        )
        
        from apps.workorders.serializers import EvidenciaSerializer
        return Response({
            "evidencia": EvidenciaSerializer(evidencia).data,
            "file_url": file_url
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {"detail": f"Error al subir archivo: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )