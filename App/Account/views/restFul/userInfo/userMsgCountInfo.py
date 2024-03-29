from django.http import JsonResponse
from django.db.models import Q
from rest_framework.views import APIView
from App.Tailwind.models import TailwindTakeOrder, TailwindRequest, DealRate
from Common.userAuthCommon import getUser, check_login
from Common.dictInfo import model_to_dict


class MeView(APIView):
    USER_INCLUDE_FIELDS = [
        'nickname', 'id',
    ]

    @check_login
    def get(self, request):
        '''
        获取当前用户的单子计数器，身份验证情况
        :param request:
        :return:
        '''
        user = getUser(request.session.get('login'))
        '''
        请求单
        未支付(unpaid) --》 支付后等待接单(paid) --》 接单后等待完成(orderT) --》 完成后变成待评价(waitR) --》评价后就完成了(accomplish)
        '''
        # 统计订单情况
        # 统计未支付的订单数量
        unpaid_number = TailwindRequest.objects.filter(
            Q(initiator=user) &
            Q(status='unpaid')
        ).count()
        # 统计等待接单订单数量
        waiting_number = TailwindRequest.objects.filter(
            Q(initiator=user) &
            Q(status='paid')
        ).count()
        # 统计(已接单)待完成订单数量
        waiting_for_finish_number = TailwindRequest.objects.filter(
            Q(initiator=user) &
            Q(status='orderT')
        ).count()
        # 统计未评价订单数量
        unrated_number = TailwindRequest.objects.filter(
            Q(initiator=user) &
            Q(status='waitR')
        ).count()
        # 统计自己正在进行中的接收单
        inProcess_number = TailwindTakeOrder.objects.filter(
            Q(mandatory=user) &
            Q(status='unaccomplished')
        ).count()

        tailwind_number = {'unpaid_number': str(unpaid_number), 'waiting_number': str(waiting_number),
                           'waiting_for_finish_number': str(waiting_for_finish_number),
                           'unrated_number': str(unrated_number), 'inProcess_number': str(inProcess_number)}

        userAuthentication = {}

        if user.user_role == '5':
            userAuthentication['email_active'] = False
        else:
            userAuthentication['email_active'] = True
        if user.student_id != 0:
            userAuthentication['es_check'] = True
        else:
            userAuthentication['es_check'] = False

        return JsonResponse({
            'status': True,
            'userAuthentication': userAuthentication,
            'tailwind_number': tailwind_number
        })
