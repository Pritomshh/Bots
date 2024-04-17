class Bot:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, bot=None):

        if hasattr(self, "_initialized"):
            return
        
        self._initialized = True

        self._bot = bot


    @property
    def bot(self):
        return self._bot

    @bot.setter
    def bot(self, bot):
        self._bot = bot

    @classmethod
    def reset_instance(cls):
        cls._instance = None
