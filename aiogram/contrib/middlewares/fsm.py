import copy

from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware
from aiogram.dispatcher.storage import FSMContext


class FSMMiddleware(LifetimeControllerMiddleware):
    skip_patterns = ['error', 'update']

    async def pre_process(self, obj, data, *args):
        proxy = await FSMSStorageProxy.create(self.manager.dispatcher.current_state())
        data['state_data'] = proxy

    async def post_process(self, obj, data, *args):
        proxy = data.get('state_data', None)
        if isinstance(proxy, FSMSStorageProxy):
            await proxy.save()


class FSMSStorageProxy(dict):
    def __init__(self, fsm_context: FSMContext):
        super().__init__()
        self.fsm_context = fsm_context
        self._copy = {}
        self._state = None
        self._is_dirty = False

    @classmethod
    async def create(cls, fsm_context: FSMContext):
        """
        :param fsm_context:
        :return:
        """
        proxy = cls(fsm_context)
        await proxy.load()
        return proxy

    async def load(self):
        self.clear()
        self._state = await self.fsm_context.get_state()
        self.update(await self.fsm_context.get_data())
        self._copy = copy.deepcopy(dict(self))
        self._is_dirty = False

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value
        self._is_dirty = True

    @state.deleter
    def state(self):
        self._state = None
        self._is_dirty = True

    async def save(self, force=False):
        if self._copy != dict(self) or force:
            await self.fsm_context.set_data(data=self)
        if self._is_dirty or force:
            await self.fsm_context.set_state(self.state)
        self._is_dirty = False
        self._copy = copy.deepcopy(dict(self))

    def __str__(self):
        s = super().__str__()
        readable_state = f"'{self.state}'" if self.state else "''"
        return f"<{self.__class__.__name__}(state={readable_state}, data={s})>"

    def clear(self):
        del self.state
        return super().clear()
