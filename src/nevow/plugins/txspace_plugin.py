from nevow import athena
from txspace import assets

myPackage = athena.JSPackage({
    'txspace': assets.get('webroot/js/client.js'),
    })

