class Captcha:
    """验证码的处理"""
    def detect_captcha(self, get_result, url):
        """进行验证码的处理"""
        session, resp = get_result
        session.close()
        return resp
