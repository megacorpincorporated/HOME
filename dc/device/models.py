import peewee

from hume_storage import PersistentModel


class Device(PersistentModel):
    uuid = peewee.CharField(unique=True)

    @staticmethod
    def local_key_field():
        """
        :return: name of local dict key field
        """
        return "uuid"
