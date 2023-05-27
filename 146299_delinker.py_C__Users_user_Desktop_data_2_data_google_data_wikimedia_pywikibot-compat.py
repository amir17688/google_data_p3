# Helper script for delinker and image_replacer

__version__ = '$Id: 2372367df54f3319508f53b66fbcabe2b4f39959 $'

import sys

sys.path.insert(0, 'commonsdelinker')

module = 'delinker'
if len(sys.argv) > 1:
    if sys.argv[1] == 'replacer':
        del sys.argv[1]
        module = 'image_replacer'

bot = __import__(module)
bot.main()
