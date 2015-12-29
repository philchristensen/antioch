#!antioch

def usage():
    write(caller, "Usage: @alias (add <alias>|remove <alias>|list) on <object>", is_error=True)

result = []
if(has_dobj_str()):
    ds = get_dobj_str()
    result = ds.split(' ', 1)
    if(len(result) != 2):
        usage()
        return
else:
    usage()
    return

sub, alias = result
if(sub == 'add'):
    obj = get_pobj('to')
    obj.add_alias(alias)
    print "Alias %r added to %s" % (alias, obj)
elif(sub == 'remove'):
    obj = get_pobj('from')
    obj.remove_alias(alias)
    print "Alias %r removed from %s" % (alias, obj)
elif(sub == 'list'):
    obj = here.find(alias)
    aliases = obj.get_aliases()
    print "%s has the following aliases: %r" % (obj, aliases)
