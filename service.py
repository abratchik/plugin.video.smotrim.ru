from resources.lib.smotrim import Smotrim
from resources.lib.users import User

if __name__ == '__main__':
    Smotrim = Smotrim()
    User = User()

    User.watch(Smotrim, "daemons")
