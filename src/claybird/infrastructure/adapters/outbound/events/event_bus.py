from claybird.application.ports.outbound.event_bus_port import EventBusPort
import inspect

class EventDescriptor:

    def __init__(self, event_name, func):
        self.event_name = event_name
        self.func = func

    def __set_name__(self, owner, name):
        EventBus.handlers.setdefault(self.event_name, []).append((owner, name))

        if not hasattr(owner, "_event_init_wrapped"):
            self.wrap_init(owner)
            owner._event_init_wrapped = True

    def wrap_init(self, owner):
        old_init = owner.__init__

        def new_init(self, *args, **kwargs):
            old_init(self, *args, **kwargs)
            EventBus.register_instance(self)

        owner.__init__ = new_init

    def __get__(self, instance, owner):
        return self.func.__get__(instance, owner)


class EventBus(EventBusPort):
    handlers = {}
    instances = {}

    @classmethod
    def on(cls, event_name: str):
        def decorator(func):
            return EventDescriptor(event_name, func)
        return decorator

    @classmethod
    def register_instance(cls, instance):
        cls.instances.setdefault(type(instance), []).append(instance)

    @classmethod
    async def emit(cls, event_name, *args, **kwargs):
        for owner_cls, func_name in cls.handlers.get(event_name, []):
            for instance in cls.instances.get(owner_cls, []):
                method = getattr(instance, func_name)

                if inspect.iscoroutinefunction(method):
                    await method(*args, **kwargs)
                else:
                    method(*args, **kwargs)

