from rest_framework import exceptions
from django.core.exceptions import PermissionDenied
import jwt
from datetime import datetime
from querystring_parser import parser
import logging
# from customer_portal.utils import Util as base_util
# from app.helper.iam.userClaim import UserClaim
logger = logging.getLogger(__name__)


def manage_queue_assignment(func):
    def wrapper(self, request, *args, **kwargs):
        try:
            bu_id_ = str(request.query_params.get('bu_id')).replace('-', '_')
            queue_name_to_use = f"dpai_service_{bu_id_}_queue"
            request.queue_name = queue_name_to_use
            print(queue_name_to_use)     
        except Exception as e:
            print("Error decoding request body:", e)
        return func(self, request, *args, **kwargs)
    return wrapper

def get_token(request):
    try:
        token = str.replace(str(request.META.get('HTTP_AUTHORIZATION')), 'Bearer ', '')
        return token
    except Exception as ex:
        logger.error(f"Error get_token: {ex}")
        raise exceptions.AuthenticationFailed('Token not received')


def get_data_from_token(token):
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded
    except jwt.ExpiredSignatureError as ex:
        logger.error(f"Error get_data_from_token: {ex}")
        raise exceptions.AuthenticationFailed('Token has expired')


def user_access_permission(**keywords):
    def decorator(view_func):
        def wrap(request, *args, **kwargs):
            bu_id_status = False
            tenant_id_status = False
            token = get_token(request)
            print(datetime.now(),"UserClaim fetch START")
            userClaim ='' #UserClaim.get(base_util.getEmailAddressFromToken(token), token)
            print(datetime.now(),"UserClaim fetch END")
            permissions = userClaim['iam/permissions'] if 'iam/permissions' in userClaim else []
            roles = userClaim['iam/roles'] if 'iam/roles' in userClaim else []
            permission_name = keywords['permissions'] if keywords['permissions'] else None           
            post_dict = parser.parse(request.GET.urlencode())
            request.userClaim = userClaim
            request.permissions = permissions
            
            if 'SYS_ADMIN' in roles:
                return view_func(request, *args, **kwargs)
            
            try:
                tenant_id = post_dict["tenant_id"]
            except Exception as ex:
                logger.error({"user_access_permission: tenant_id not passed": f"{ex}"})
                raise PermissionDenied

            try:
                bu_id = post_dict["bu_id"]
                if any(bu['id'] == bu_id for bu in userClaim['business_units']):
                    bu_id_status = True
                    bu = next((bu for bu in userClaim['business_units'] if bu['id'] == bu_id), None)
                    permissions = bu['permissions']
                    request.permissions = permissions
                    roles = bu['roles']
            except Exception as ex:
                logger.error({"user_access_permission: bu_id not passed": f"{ex}"})

            try:
                if userClaim['tenant_id'] == tenant_id and (True if "*" in permission_name else any(perm in permission_name for perm in permissions)):
                    tenant_id_status = True
            except Exception as ex:
                logger.error({"user_access_permission: Permission Denied": f"{ex}"})
                raise PermissionDenied

            if not permission_name or not bu_id_status or not tenant_id_status:
                logger.error({"user_access_permission: Permission Denied": f"userClaim: {userClaim}, PERMISSION: {permission_name}, BUID: {bu_id_status}, TENANTID: {tenant_id_status}"})
                raise PermissionDenied

            if '*' in permission_name:
                return view_func(request, *args, **kwargs)
            elif any(perm in permission_name for perm in permissions):
                return view_func(request, *args, **kwargs)                      
            else:                    
                logger.error("user_access_permission: Permission Denied")
                raise PermissionDenied
                
        return wrap

    return decorator
