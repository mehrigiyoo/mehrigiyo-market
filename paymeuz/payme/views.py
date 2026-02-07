# import json
# import logging
# from django.http import JsonResponse
# from django.views import View
# from django.views.decorators.csrf import csrf_exempt
# from django.utils.decorators import method_decorator
#
# from paymeuz.payme.service import PaymeService
#
# logger = logging.getLogger(__name__)
#
#
# @method_decorator(csrf_exempt, name='dispatch')
# class PaymeCallbackView(View):
#     """
#     Payme Merchant API callback endpoint
#
#     Payme will call this URL with JSON-RPC 2.0 format
#     """
#
#     def post(self, request):
#         """Handle Payme callback"""
#
#         # 1. Check authentication
#         if not PaymeService.check_auth(request):
#             return JsonResponse({
#                 'error': {
#                     'code': -32504,
#                     'message': 'Unauthorized'
#                 }
#             }, status=401)
#
#         # 2. Parse request
#         try:
#             data = json.loads(request.body.decode('utf-8'))
#         except json.JSONDecodeError:
#             return JsonResponse({
#                 'error': {
#                     'code': -32700,
#                     'message': 'Parse error'
#                 }
#             })
#
#         method = data.get('method')
#         params = data.get('params', {})
#         request_id = data.get('id')
#
#         logger.info(f"Payme callback: {method} - Params: {params}")
#
#         # 3. Route to appropriate handler
#         response_data = self.handle_method(method, params)
#
#         # 4. Build JSON-RPC response
#         response = {
#             'jsonrpc': '2.0',
#             'id': request_id,
#         }
#
#         if 'error' in response_data:
#             response['error'] = response_data['error']
#         else:
#             response['result'] = response_data.get('result', {})
#
#         logger.info(f"Payme response: {response}")
#
#         return JsonResponse(response)
#
#     def handle_method(self, method, params):
#         """Route request to appropriate method"""
#
#         handlers = {
#             'CheckPerformTransaction': PaymeService.check_perform_transaction,
#             'CreateTransaction': PaymeService.create_transaction,
#             'PerformTransaction': PaymeService.perform_transaction,
#             'CheckTransaction': PaymeService.check_transaction,
#             'CancelTransaction': PaymeService.cancel_transaction,
#         }
#
#         handler = handlers.get(method)
#
#         if not handler:
#             return {
#                 'error': {
#                     'code': -32601,
#                     'message': 'Method not found'
#                 }
#             }
#
#         try:
#             return handler(params)
#         except Exception as e:
#             logger.error(f"Payme handler error: {e}", exc_info=True)
#             return {
#                 'error': {
#                     'code': -32400,
#                     'message': 'Internal error',
#                     'data': str(e)
#                 }
#             }