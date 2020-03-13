# use own dns resolver instance string replace ?

DOMAIN_RESOLVE = dict()

DOMAIN_RESOLVE['oauth.secure.pixiv.net'] = [
    '210.140.131.220'
]

DOMAIN_RESOLVE['tc-pximg01.techorus-cdn.com'] = [
    # although 'tc-pximg01.techorus-cdn.com' can direction connect,
    # but direction connection speed is slow.
    '23.211.136.40',
    '23.200.142.8',
    '23.200.142.43',
    '23.218.94.57',
    '219.76.10.24',
    '219.76.10.27'
]

DOMAIN_RESOLVE['public-api.secure.pixiv.net'] = [
    '210.140.131.223',
    '210.140.131.220'
]
