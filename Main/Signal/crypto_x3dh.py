from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey, X25519PublicKey
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey
)
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.exceptions import InvalidSignature

from typing import Optional, Tuple, Dict


# ---------- key serialization helpers ----------
def x25519_priv_to_bytes(priv: X25519PrivateKey) -> bytes:
    return priv.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )


def x25519_pub_to_bytes(pub: X25519PublicKey) -> bytes:
    return pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )


def x25519_priv_from_bytes(b: bytes) -> X25519PrivateKey:
    return X25519PrivateKey.from_private_bytes(b)


def x25519_pub_from_bytes(b: bytes) -> X25519PublicKey:
    return X25519PublicKey.from_public_bytes(b)


def ed25519_priv_to_bytes(priv: Ed25519PrivateKey) -> bytes:
    return priv.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )


def ed25519_pub_to_bytes(pub: Ed25519PublicKey) -> bytes:
    return pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )


def ed25519_priv_from_bytes(b: bytes) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(b)


def ed25519_pub_from_bytes(b: bytes) -> Ed25519PublicKey:
    return Ed25519PublicKey.from_public_bytes(b)


# ---------- key generation ----------
def generate_identity_keypair() -> Tuple[X25519PrivateKey, Ed25519PrivateKey]:
    """
    Returns (X25519 identity private key, Ed25519 signing private key).
    We separate X25519 for DH and Ed25519 for signing SPK (per reference implementation patterns).
    """
    ik_priv = X25519PrivateKey.generate()
    sig_priv = Ed25519PrivateKey.generate()
    return ik_priv, sig_priv


def generate_x25519_keypair() -> X25519PrivateKey:
    return X25519PrivateKey.generate()


# ---------- signed prekey creation ----------
def create_signed_prekey(spk_priv: X25519PrivateKey, signer_priv: Ed25519PrivateKey) -> Tuple[bytes, bytes]:
    """
    Returns (spk_pub_bytes, signature_bytes) where signature is Ed25519(sign(spk_pub_bytes)).
    """
    spk_pub = x25519_pub_to_bytes(spk_priv.public_key())
    signature = signer_priv.sign(spk_pub)
    return spk_pub, signature


def verify_signed_prekey(spk_pub_bytes: bytes, signature: bytes, signer_pub: Ed25519PublicKey) -> bool:
    try:
        signer_pub.verify(signature, spk_pub_bytes)
        return True
    except InvalidSignature:
        return False


# ---------- prekey bundle ----------
def make_prekey_bundle(
    identity_pub_bytes: bytes,
    spk_pub_bytes: bytes,
    spk_signature: bytes,
    one_time_prekey_pub_bytes: Optional[bytes] = None
) -> Dict:
    """
    Bundle the public components that would be stored on the server.
    """
    bundle = {
        "identity_key": identity_pub_bytes,  # X25519 pub bytes
        "signed_prekey": spk_pub_bytes,      # X25519 pub bytes
        "signed_prekey_sig": spk_signature,  # signature over SPK
    }
    if one_time_prekey_pub_bytes is not None:
        bundle["one_time_prekey"] = one_time_prekey_pub_bytes
    return bundle


# ---------- X3DH shared secret computation ----------
def _dh(priv: X25519PrivateKey, pub_bytes: bytes) -> bytes:
    pub = x25519_pub_from_bytes(pub_bytes)
    shared = priv.exchange(pub)  # returns raw 32 bytes
    return shared


def compute_x3dh_shared_secret_initiator(
    ik_a_priv: X25519PrivateKey,
    e_a_priv: X25519PrivateKey,
    ik_b_pub_bytes: bytes,
    spk_b_pub_bytes: bytes,
    opk_b_pub_bytes: Optional[bytes] = None
) -> bytes:
    """
    Initiator A computes:
      DH1 = DH(IK_A_priv, SPK_B_pub)
      DH2 = DH(E_A_priv, IK_B_pub)
      DH3 = DH(E_A_priv, SPK_B_pub)
      DH4 = DH(E_A_priv, OPK_B_pub) optional
    Then HKDF over the concatenation (DH1||DH2||DH3||DH4) to produce symmetric key.
    """
    dh1 = _dh(ik_a_priv, spk_b_pub_bytes)
    dh2 = _dh(e_a_priv, ik_b_pub_bytes)
    dh3 = _dh(e_a_priv, spk_b_pub_bytes)
    parts = dh1 + dh2 + dh3
    if opk_b_pub_bytes is not None:
        dh4 = _dh(e_a_priv, opk_b_pub_bytes)
        parts += dh4

    # HKDF to derive 32-byte master secret
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"X3DH:master",
    )
    master = hkdf.derive(parts)
    return master


def compute_x3dh_shared_secret_responder(
    spk_b_priv: X25519PrivateKey,
    ik_b_priv: X25519PrivateKey,
    opk_b_priv: Optional[X25519PrivateKey],
    ik_a_pub_bytes: bytes,
    e_a_pub_bytes: bytes
) -> bytes:
    """
    Responder B computes same DHs but using its private keys:
      DH1 = DH(IK_A_pub, SPK_B_priv) -> same as DH(IK_A_priv, SPK_B_pub)
      DH2 = DH(E_A_pub, IK_B_priv) -> same as DH(E_A_priv, IK_B_pub)
      DH3 = DH(E_A_pub, SPK_B_priv) -> same as DH(E_A_priv, SPK_B_pub)
      DH4 = DH(E_A_pub, OPK_B_priv) optional
    """
    # note: swap order of args in X25519 exchange yields identical shared secret
    dh1 = spk_b_priv.exchange(x25519_pub_from_bytes(ik_a_pub_bytes))
    dh2 = ik_b_priv.exchange(x25519_pub_from_bytes(e_a_pub_bytes))
    dh3 = spk_b_priv.exchange(x25519_pub_from_bytes(e_a_pub_bytes))
    parts = dh1 + dh2 + dh3
    if opk_b_priv is not None:
        dh4 = opk_b_priv.exchange(x25519_pub_from_bytes(e_a_pub_bytes))
        parts += dh4

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"X3DH:master",
    )
    master = hkdf.derive(parts)
    return master


# ---------- convenience: serialize public keys for transport ----------
def pack_x25519_pub(pub: X25519PublicKey) -> bytes:
    return x25519_pub_to_bytes(pub)


def pack_x25519_priv(priv: X25519PrivateKey) -> bytes:
    return x25519_priv_to_bytes(priv)


def pack_ed25519_pub(pub: Ed25519PublicKey) -> bytes:
    return ed25519_pub_to_bytes(pub)


def pack_ed25519_priv(priv: Ed25519PrivateKey) -> bytes:
    return ed25519_priv_to_bytes(priv)
