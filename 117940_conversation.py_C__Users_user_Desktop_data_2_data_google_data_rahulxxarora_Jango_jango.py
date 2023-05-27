from brain import Brain

def handleForever():
   brain = Brain()
   while True:
      text = raw_input("-> ")
      brain.query(text)

