from hashlib import md5

HashValueList = [
    'fa2dd61d432f71f9dd8c745634b0d9c0',
    'ac31461eb2b973156a6d1a6fc0f4aa89',
    '93ba82ceea717ed147bc6fc706dea6e9',
    'afe50d4f79641e874c60adf60a8ec733',
    'de98e1d31b5be307c882b114245a2eee',
    '363aba815fcc049a2f9723af876af8a4',
    'b15c113aeddbeb606d938010b88cf8e6',
    'e3b63a0b1b4f4ca82cf2a5c686d58ae1'
]


def equal(data: bytes) -> bool:
    m = md5()
    m.update(data)
    value = m.hexdigest()
    if value in HashValueList:
        return True
    else:
        return False
