#!/usr/bin/env python3
# Copyright (c) 2014-2020 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test the -alertnotify, -blocknotify and -walletnotify options."""
import os

from test_framework.address import ADDRESS_BCRT1_UNSPENDABLE
from test_framework.descriptors import descsum_create
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import (
    assert_equal,
)

# Linux allow all characters other than \x00
# Windows disallow control characters (0-31) and /\?%:|"<>
FILE_CHAR_START = 32 if os.name == 'nt' else 1
FILE_CHAR_END = 128
FILE_CHARS_DISALLOWED = '/\\?%*:|"<>' if os.name == 'nt' else '/'
UNCONFIRMED_HASH_STRING = 'unconfirmed'

def notify_outputname(walletname, txid):
    return txid if os.name == 'nt' else '{}_{}'.format(walletname, txid)


class NotificationsTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 2
        self.setup_clean_chain = True

    def setup_network(self):
        self.wallet = ''.join(chr(i) for i in range(FILE_CHAR_START, FILE_CHAR_END) if chr(i) not in FILE_CHARS_DISALLOWED)
        self.alertnotify_dir = os.path.join(self.options.tmpdir, "alertnotify")
        self.blocknotify_dir = os.path.join(self.options.tmpdir, "blocknotify")
        self.walletnotify_dir = os.path.join(self.options.tmpdir, "walletnotify")
        os.mkdir(self.alertnotify_dir)
        os.mkdir(self.blocknotify_dir)
        os.mkdir(self.walletnotify_dir)

        # -alertnotify and -blocknotify on node0, walletnotify on node1
        self.extra_args = [[
            "-alertnotify=echo > {}".format(os.path.join(self.alertnotify_dir, '%s')),
            "-blocknotify=echo > {}".format(os.path.join(self.blocknotify_dir, '%s')),
        ], [
            "-rescan",
            "-walletnotify=echo %h_%b > {}".format(os.path.join(self.walletnotify_dir, notify_outputname('%w', '%s'))),
        ]]
        self.wallet_names = [self.default_wallet_name, self.wallet]
        super().setup_network()

    def run_test(self):
        if self.is_wallet_compiled():
            # Setup the descriptors to be imported to the wallet
            seed = "cTdGmKFWpbvpKQ7ejrdzqYT2hhjyb3GPHnLAK7wdi5Em67YLwSm9"
            xpriv = "tprv8ZgxMBicQKsPfHCsTwkiM1KT56RXbGGTqvc2hgqzycpwbHqqpcajQeMRZoBD35kW4RtyCemu6j34Ku5DEspmgjKdt2qe4SvRch5Kk8B8A2v"
            desc_imports = [{
                "desc": descsum_create("wpkh(" + xpriv + "/0/*)"),
                "timestamp": 0,
                "active": True,
                "keypool": True,
            },{
                "desc": descsum_create("wpkh(" + xpriv + "/1/*)"),
                "timestamp": 0,
                "active": True,
                "keypool": True,
                "internal": True,
            }]
            # Make the wallets and import the descriptors
            # Ensures that node 0 and node 1 share the same wallet for the conflicting transaction tests below.
            for i, name in enumerate(self.wallet_names):
                self.nodes[i].createwallet(wallet_name=name, descriptors=self.options.descriptors, blank=True, load_on_startup=True)
                if self.options.descriptors:
                    self.nodes[i].importdescriptors(desc_imports)
                else:
                    self.nodes[i].sethdseed(True, seed)

        self.log.info("test -blocknotify")
        block_count = 10
        blocks = self.nodes[1].generatetoaddress(block_count, self.nodes[1].getnewaddress() if self.is_wallet_compiled() else ADDRESS_BCRT1_UNSPENDABLE)

        # wait at most 10 seconds for expected number of files before reading the content
        self.wait_until(lambda: len(os.listdir(self.blocknotify_dir)) == block_count, timeout=10)

        # directory content should equal the generated blocks hashes
        assert_equal(sorted(blocks), sorted(os.listdir(self.blocknotify_dir)))

        if self.is_wallet_compiled():
            self.log.info("test -walletnotify")
            # wait at most 10 seconds for expected number of files before reading the content
            self.wait_until(lambda: len(os.listdir(self.walletnotify_dir)) == block_count, timeout=10)

            # directory content should equal the generated transaction hashes
            tx_details = list(map(lambda t: (t['txid'], t['blockheight'], t['blockhash']), self.nodes[1].listtransactions("*", block_count)))
            self.stop_node(1)
            self.expect_wallet_notify(tx_details)

            self.log.info("test -walletnotify after rescan")
            # restart node to rescan to force wallet notifications
            self.start_node(1)
            self.connect_nodes(0, 1)

            self.wait_until(lambda: len(os.listdir(self.walletnotify_dir)) == block_count, timeout=10)

            # directory content should equal the generated transaction hashes
            tx_details = list(map(lambda t: (t['txid'], t['blockheight'], t['blockhash']), self.nodes[1].listtransactions("*", block_count)))
            self.expect_wallet_notify(tx_details)

            # Conflicting transactions tests.
            # Generate spends from node 0, and check notifications
            # triggered by node 1
            self.log.info("test -walletnotify with conflicting transactions")
            self.nodes[0].rescanblockchain()
            self.nodes[0].generatetoaddress(100, ADDRESS_BCRT1_UNSPENDABLE)
            self.sync_blocks()

            # Generate transaction on node 0, sync mempools, and check for
            # notification on node 1.
            tx1 = self.nodes[0].sendtoaddress(address=ADDRESS_BCRT1_UNSPENDABLE, amount=1)
            assert_equal(tx1 in self.nodes[0].getrawmempool(), True)
            self.sync_mempools()
            self.expect_wallet_notify([(tx1, -1, UNCONFIRMED_HASH_STRING)])

        # TODO: add test for `-alertnotify` large fork notifications

    def expect_wallet_notify(self, tx_details):
        self.wait_until(lambda: len(os.listdir(self.walletnotify_dir)) >= len(tx_details), timeout=10)
        # Should have no more and no less files than expected
        assert_equal(sorted(notify_outputname(self.wallet, tx_id) for tx_id, _, _ in tx_details), sorted(os.listdir(self.walletnotify_dir)))
        # Should now verify contents of each file
        for tx_id, blockheight, blockhash in tx_details:
            fname = os.path.join(self.walletnotify_dir, notify_outputname(self.wallet, tx_id))
            # Wait for the cached writes to hit storage
            self.wait_until(lambda: os.path.getsize(fname) > 0, timeout=10)
            with open(fname, 'rt', encoding='utf-8') as f:
                text = f.read()
                # Universal newline ensures '\n' on 'nt'
                assert_equal(text[-1], '\n')
                text = text[:-1]
                if os.name == 'nt':
                    # On Windows, echo as above will append a whitespace
                    assert_equal(text[-1], ' ')
                    text = text[:-1]
                expected = str(blockheight) + '_' + blockhash
                assert_equal(text, expected)

        for tx_file in os.listdir(self.walletnotify_dir):
            os.remove(os.path.join(self.walletnotify_dir, tx_file))


if __name__ == '__main__':
    NotificationsTest().main()
