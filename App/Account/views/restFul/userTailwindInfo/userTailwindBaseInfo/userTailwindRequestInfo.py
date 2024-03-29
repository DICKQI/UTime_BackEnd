from App.Tailwind.models import TailwindRequest
from django.http import JsonResponse
from django.utils.timezone import now
from django.db.models import Q
from Common.paginator import paginator
from Common.dictInfo import model_to_dict
from Common.userAuthCommon import check_login, getUser, checkStudent
from Common.dateInfo import get_three_month_ago, generateFormatTime
from rest_framework.views import APIView
import json, datetime


def generateRequestID():
    # 根据时间生成请求单id
    time = generateFormatTime()
    oldRequest = TailwindRequest.objects.first()
    if not oldRequest:  # 这个if应该只用得上一次
        # 如果一个订单都没有
        newID = time + '0001'
        return int(newID)
    # 获取最新订单的时间
    oldOrderTime = str(oldRequest.requestID)[:len(str(oldRequest.requestID)) - 4]
    if oldOrderTime == time:
        # 判断是否是同一分钟创建的
        newID = str(int(str(oldRequest.requestID)[-4:]) + 1)
    else:
        # 非同一分钟创建
        newID = '0001'
    for i in range(4 - len(newID)):
        newID = '0' + newID
    newID = time + newID
    return int(newID)


class UserTailwindRequestView(APIView):
    """用户对发起单的一系列操作"""
    COMMON_FIELDS = [
        'requestID', 'taskContent', 'beginTime', 'endTime',
        'money', 'serviceType', 'status'
    ]

    @check_login
    # @checkStudent
    def get(self, request):
        """
        获得用户发起的订单
        :param request:
        :return:
        """
        try:
            user = getUser(email=request.session.get('login'))
            page = request.GET.get('page')
            ago = request.GET.get('ago')
            types = request.GET.get('type')
            three_month_ago = get_three_month_ago()
            type_list = ['unpaid', 'paid', 'orderT', 'waitR', 'accomplish', 'cancel']
            if not types:  # 没有对应的url参数，查询全部类型的
                types = type_list
            elif types not in type_list:  # 参数不合法
                types = ['unpaid']
            else:  # 参数合法，查询对应类型
                types = [types]
            if ago:
                # 获取三个月前的订单
                tailwindObj = TailwindRequest.objects.filter(
                    Q(initiator=user)
                    & Q(beginTime__lte=three_month_ago)
                    & Q(status__in=types)
                )
            else:
                # 获取三个月内的
                tailwindObj = TailwindRequest.objects.filter(
                    Q(initiator=user)
                    & Q(beginTime__gte=three_month_ago)
                    & Q(status__in=types)
                )
            tailwindList = paginator(tailwindObj, page)
            tailwind = [model_to_dict(t, fields=self.COMMON_FIELDS) for t in tailwindList]
            return JsonResponse({
                'status': True,
                'tailwind': tailwind,
                'has_next': tailwindList.has_next(),
                'has_previous': tailwindList.has_previous()
            })
        except Exception as ex:
            return JsonResponse({
                'status': False,
                'errMsg': '错误信息：' + str(ex)
            }, status=403)

    @check_login
    # @checkStudent
    def post(self, request):
        """
        用户发起订单
        :param request:
        :return:
        """
        try:
            user = getUser(email=request.session.get('login'))
            jsonParam = json.loads((request.body).decode('utf-8'))

            taskContent = jsonParam.get('taskContent')
            serviceType = jsonParam.get('type')
            beginPlace = jsonParam.get('begin_place')
            endPlace = jsonParam.get('end_place')
            money = float(jsonParam.get('money'))
            endTime = datetime.datetime.strptime(jsonParam.get('end_time'), '%Y-%m-%d %H:%M:%S')

            newTailwindRequest = TailwindRequest.objects.create(
                requestID=generateRequestID(),
                taskContent=taskContent,
                serviceType=serviceType,
                beginPlace=beginPlace,
                endPlace=endPlace,
                money=money,
                endTime=endTime,
                beginTime=now(),
                initiator=user
            )

            return JsonResponse({
                'status': True,
                'id': newTailwindRequest.requestID,
            })

        except Exception as ex:
            return JsonResponse({
                'status': False,
                'errMsg': '错误信息：' + str(ex)
            }, status=403)

    @check_login
    # @checkStudent
    def put(self, requests, tid):
        '''
        用户为发起单添加图片
        :param requests:
        :param tid:
        :return:
        '''
        try:
            tr = TailwindRequest.objects.filter(requestID=tid)
            if not tr.exists:
                return JsonResponse({
                    'status': False,
                    'errMsg': '请求单不存在'
                }, status=404)
            tr = tr[0]
            user = getUser(requests.session.get('login'))
            if tr.initiator != user:
                return JsonResponse({
                    'status': False,
                    'errMsg': '你没有权限操作'
                }, status=401)
            get_img = requests.FILES.get("img")
            tr.img = get_img
            tr.save()
            return JsonResponse({
                'status': True,
                'id': tr.requestID
            })

        except Exception as ex:
            return JsonResponse({
                'status': False,
                'errMsg': '错误信息：' + str(ex)
            }, status=403)

    @check_login
    def delete(self, requests, tid):
        """
        用户删除发起单
        :param request:
        :param tid:
        :return:
        """
        try:
            tr = TailwindRequest.objects.filter(requestID=tid)
            if not tr.exists:
                return JsonResponse({
                    'status': False,
                    'errMsg': '请求单不存在'
                }, status=404)
            tr = tr[0]
            user = getUser(requests.session.get('login'))
            if tr.initiator != user:
                return JsonResponse({
                    'status': False,
                    'errMsg': '你没有权限操作'
                }, status=401)
            if tr.status == 'paid':
                # 退款
                pass
            elif tr.status == 'orderT':
                # 告知接单者，同意后退款
                pass
        except Exception as ex:
            return JsonResponse({
                'status': False,
                'errMsg': '错误信息：' + str(ex)
            })
