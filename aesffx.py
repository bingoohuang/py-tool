#!/usr/bin/env python3
"""

https://stackoverflow.com/questions/196017/unique-non-repeating-random-numbers-in-o1/16097246#16097246

You could use Format-Preserving Encryption to encrypt a counter. Your counter just goes from 0 upwards,
 and the encryption uses a key of your choice to turn it into a seemingly random value
 of whatever radix and width you want. E.g. for the example in this question: radix 10, width 3.

Block ciphers normally have a fixed block size of e.g. 64 or 128 bits. But Format-Preserving Encryption
allows you to take a standard cipher like AES and make a smaller-width cipher, of whatever radix
and width you want, with an algorithm which is still cryptographically robust.

It is guaranteed to never have collisions (because cryptographic algorithms create a 1:1 mapping).
It is also reversible (a 2-way mapping), so you can take the resulting number and get back to the counter value
you started with.

This technique doesn't need memory to store a shuffled array etc, which can be an advantage
on systems with limited memory.

AES-FFX is one proposed standard method to achieve this. I've experimented with some basic Python code
which is based on the AES-FFX idea, although not fully conformant--see Python code here.
It can e.g. encrypt a counter to a random-looking 7-digit decimal number, or a 16-bit number.
Here is an example of radix 10, width 3 (to give a number between 0 and 999 inclusive) as the question stated:

000   733
001   374
002   882
003   684
004   593
005   578
006   233
007   811
008   072
009   337
010   119
011   103
012   797
013   257
014   932
015   433
...   ...
To get different non-repeating pseudo-random sequences, change the encryption key.
Each encryption key produces a different non-repeating pseudo-random sequence.



Format-preserving encryption.
See proposed AES-FFX specs:
    http://csrc.nist.gov/groups/ST/toolkit/BCM/documents/proposedmodes/ffx/ffx-spec.pdf
    http://csrc.nist.gov/groups/ST/toolkit/BCM/documents/proposedmodes/ffx/ffx-spec2.pdf
This uses the overall principles of AES-FFX, method 2. It doesn't conform to the proposed
FFX-A2, FFX-A10, or FFX[radix] standards.
Dependencies:
- Python 3
- PyCrypto
License: MIT
MIT license statement is as follows:
----------------------------------------------------------------------------
Copyright (c) 2012 Craig McQueen
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
----------------------------------------------------------------------------
"""

# Standard Python library modules
import struct
import time
from datetime import timedelta

# pip3 uninstall Crypto
# pip3 uninstall pycrypto
# pip3 install pycrypto

# 3rd-party modules
from Crypto.Cipher import AES


class FPEInteger:
    """
    Format-Preserving Encryption.
    This uses AES, but it does not conform to the proposed AES-FFX[radix] standard.
    Inputs and outputs for encryption and decryption are integers.
    This should be suitable for block sizes of up to 2**96.
    """

    def __init__(self, key, rounds=10, radix=2, width=32):
        """key is a 16- 24- or 32-byte string."""
        self.aes_obj = AES.new(key, AES.MODE_ECB)
        self.rounds = rounds
        part_widths = [(width + 1) // 2, width // 2]
        self.modulos = [radix ** part_width for part_width in part_widths]

        # Pick a suitable block encryption function, with a large enough block size, and also
        # keeping any bias of the final modulo operation reasonably small.
        block_size = radix ** width
        self.block_size = block_size
        if ((block_size <= 2 ** 32) or
                ((block_size <= 2 ** 64) and ((2 ** 128 % block_size) == 0))):
            self.block_encrypt_func = self.block_encrypt_func_small
        else:
            self.block_encrypt_func = self.block_encrypt_func_large

    def split_message(self, message):
        """Split message into working parts. Return a list of parts."""
        work_0 = message % self.modulos[0]
        message //= self.modulos[0]
        work_1 = message % self.modulos[1]
        return [work_0, work_1]

    def join_message(self, work):
        """Join list of message parts back into message. Return the message.
        Inverse of self.split_message()."""
        return (work[1] * self.modulos[0]) + work[0]

    def block_encrypt_func_small(self, work_val, round_num, out_modulo):
        """Block encryption function--small one for block size 2**32 or smaller."""
        byte_data = struct.pack("<QQ", round_num, work_val)
        encrypt_data = self.aes_obj.encrypt(byte_data)
        temp, = struct.unpack("<8xQ", encrypt_data)
        temp %= out_modulo
        return temp

    def block_encrypt_func_large(self, work_val, round_num, out_modulo):
        """Block encryption function--large one for block size bigger than 2**32."""
        byte_data = struct.pack("<QQ", round_num, work_val)
        encrypt_data = self.aes_obj.encrypt(byte_data)
        temp_lo, temp_hi = struct.unpack("<QQ", encrypt_data)
        temp = (temp_hi << 64) | temp_lo
        temp %= out_modulo
        return temp

    def encrypt(self, message):
        """message is an integer. Returns an integer."""
        work = self.split_message(message)
        i_from, i_to = 0, 1
        for round_num in range(self.rounds):
            temp = self.block_encrypt_func(work[i_from], round_num, self.modulos[i_to])
            work[i_to] = (work[i_to] + temp) % self.modulos[i_to]
            i_from, i_to = i_to, i_from
        return self.join_message(work)

    def decrypt(self, message):
        """message is an integer. Returns an integer."""
        work = self.split_message(message)
        i_from, i_to = (self.rounds - 1) % 2, self.rounds % 2
        for round_num in range(self.rounds - 1, -1, -1):
            temp = self.block_encrypt_func(work[i_from], round_num, self.modulos[i_to])
            work[i_to] = (work[i_to] - temp) % self.modulos[i_to]
            i_from, i_to = i_to, i_from
        return self.join_message(work)


if __name__ == "__main__":
    radix = 10
    width = 7
    # 3 rounds is a minimum for "statistically adequate" shuffling (but not
    # cryptographically secure). If it's less than that, there is statistical
    # correlation between samples separated by radix**(width//2).
    rounds = 10
    should_print = True

    fpe_obj = FPEInteger(key=b"yourkeyhere16bit", rounds=rounds, radix=radix, width=width)
    # print("Using block encrypt function '{0}'".format(fpe_obj.block_encrypt_func.__name__))

    if should_print:
        print("Radix {0}, width {1}".format(radix, width))
        if radix == 10:
            print_base = 'd'
            print_width = width
        elif radix == 8:
            print_base = 'o'
            print_width = width
        else:
            print_base = 'X'
            print_width = 1
            while 16 ** print_width < fpe_obj.block_size:
                print_width += 1
        print("Printing as format '{0}', width {1}".format(print_base, print_width))

    encrypted_outputs = set()
    start = 0
    run_range = 1000000
    start_time = time.monotonic()
    # run_range = radix**width
    for i in range(start, start + run_range):
        try:
            encrypted = fpe_obj.encrypt(i)
            decrypted = fpe_obj.decrypt(encrypted)
            if should_print and (i < 10 or i > run_range - 10):
                print("{0:0{width}{base}}   {1:0{width}{base}}".format(i, encrypted, decrypted,
                                                                       width=print_width, base=print_base))
            assert (encrypted not in encrypted_outputs)
            encrypted_outputs.add(encrypted)
            assert (i == decrypted)
        except KeyboardInterrupt:
            print('Completed {0} calculations'.format(i))
            break

    # https://stackoverflow.com/questions/1557571/how-do-i-get-time-of-a-python-programs-execution
    end_time = time.monotonic()
    print(timedelta(seconds=end_time - start_time))

"""Output:
Radix 10, width 7
Printing as format 'd', width 7
0000000   7476086
0000001   6861324
0000002   2578807
0000003   8655078
0000004   1326749
0000005   2936356
0000006   1009534
0000007   1127857
0000008   1711684
0000009   8330130
0999991   8924997
0999992   9217666
0999993   7328730
0999994   1999893
0999995   3445725
0999996   3340822
0999997   9459211
0999998   7954412
0999999   0585854
0:00:31.457330
"""
