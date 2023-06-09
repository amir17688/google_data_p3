from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from orchestra.bots.errors import SlackCommandInvalidRequest
from orchestra.bots.basebot import BaseBot
from orchestra.bots.staffbot import StaffBot


@method_decorator(csrf_exempt, name='dispatch')
class BotMixin(View):
    """
    Generic mixin to handle messages to bots, should be used by specifying
    a `BotClass` to instantiate with the request data.
    """
    BotClass = BaseBot
    bot_config = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = self.BotClass(**self.bot_config)

    def post(self, request, *args, **kwargs):
        data = request.POST
        try:
            response_data = self.bot.dispatch(data)
        except SlackCommandInvalidRequest as e:
            response_data = {'error': str(e)}
        return JsonResponse(response_data)


class StaffBotView(BotMixin):
    BotClass = StaffBot
