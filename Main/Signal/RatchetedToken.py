class RatchetedToken:
    def __init__(self, innerToken, ratchet):
        self.innerToken = innerToken
        self.ratchet = ratchet

    async def _Send(self, mail):
        mail.content = self.ratchet.encrypt(mail.content)
        return await self.innerToken.Send(mail)

    async def _Receive(self):
        result = await self.innerToken.Receive()
        if not hasattr(result, "status") or result.status != 0:
            return result
        decrypted = []
        for mail in result.inbox:
            mail.content = self.ratchet.decrypt(mail.content)
            decrypted.append(mail)
        result.inbox = decrypted
        return result
