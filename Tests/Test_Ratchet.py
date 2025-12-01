# -*- coding: utf-8 -*-
import unittest
from Main.Signal.Ratchet import Ratchet
from Main.Signal.IRatchet import IRatchet
import base64
import os


class TestRatchet(unittest.TestCase):

    def make_init(self):
        root_key = base64.b64encode(os.urandom(32)).decode()
        return IRatchet.InitData(root_key=root_key)

    def test_encrypt_decrypt(self):
        initA = self.make_init()
        initB = self.make_init()

        A = Ratchet(initA)
        B = Ratchet(initB)

        # simulate handshake exchange of DH pubkeys
        A.data.dh_remote_pub = base64.b64encode(B.dh_self_pub.public_bytes_raw()).decode()
        B.data.dh_remote_pub = base64.b64encode(A.dh_self_pub.public_bytes_raw()).decode()

        msg = "hello world"
        send_data = IRatchet.SendData(msg)
        out = A.Send(send_data)

        recv_data = IRatchet.ReceiveData(out.ciphertext, out.header)
        received = B.Receive(recv_data)

        self.assertEqual(received.plaintext, msg)

    def test_multiple_messages(self):
        initA = self.make_init()
        initB = self.make_init()

        A = Ratchet(initA)
        B = Ratchet(initB)

        # exchange pubkeys
        A.data.dh_remote_pub = base64.b64encode(B.dh_self_pub.public_bytes_raw()).decode()
        B.data.dh_remote_pub = base64.b64encode(A.dh_self_pub.public_bytes_raw()).decode()

        msgs = ["one", "two", "three"]
        for m in msgs:
            out = A.Send(IRatchet.SendData(m))
            received = B.Receive(IRatchet.ReceiveData(out.ciphertext, out.header))
            self.assertEqual(received.plaintext, m)


if __name__ == "__main__":
    unittest.main()
