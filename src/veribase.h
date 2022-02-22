// Copyright (c) 2022 barrystyle
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#ifndef BITCOIN_VERIBASE_H
#define BITCOIN_VERIBASE_H

namespace veribase
{
        bool IsVerium();
        void SetVerium(bool& mode);
        const unsigned int NetworkMaxHeadersResults();
        const unsigned int NetworkMaxFutureBlockTime();
        const unsigned int NetworkMaxMsgSize();
        const char* DaemonPidFileName();
}

#endif // BITCOIN_VERIBASE_H

