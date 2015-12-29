#!antioch

obj = args[0]
obj.allow('wizards', 'anything')
obj.allow('owners', 'anything')

if(obj.get_type() == 'verb'):
    obj.allow('everyone', 'execute')
else:
    obj.allow('everyone', 'read')