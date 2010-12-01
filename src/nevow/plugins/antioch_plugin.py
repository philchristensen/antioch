from nevow import athena
from antioch import assets

myPackage = athena.JSPackage({
    'antioch': assets.get('webroot/js/client.js'),
    })

