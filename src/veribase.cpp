// Copyright (c) 2022 barrystyle
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <veribase.h>

namespace veribase
{
        bool isVerium = false;

        const unsigned int VERIUM_MSGMAX = 4000000;
        const unsigned int VERICOIN_MSGMAX = 33554432;
        const char* VERIUM_PID_FILENAME = "veriumd.pid";
        const char* VERICOIN_PID_FILENAME = "vericoind.pid";
        const unsigned int VERIUM_MAXFUTUREBLKTIME = 2 * 60 * 60;
        const unsigned int VERICOIN_MAXFUTUREBLKTIME = 10 * 60;
        const unsigned int VERIUM_MAXHEADERSRESULTS = 8000;
        const unsigned int VERICOIN_MAXHEADERSRESULTS = 100000;

        bool IsVerium() {
            return isVerium;
        }

        void SetVerium(bool& mode) {
            isVerium = mode;
        }

        const unsigned int NetworkMaxHeadersResults() {
            return isVerium ? VERIUM_MAXHEADERSRESULTS : VERICOIN_MAXHEADERSRESULTS;
        }

        const unsigned int NetworkMaxFutureBlockTime() {
            return isVerium ? VERIUM_MAXFUTUREBLKTIME : VERICOIN_MAXFUTUREBLKTIME;
        }

        const unsigned int NetworkMaxMsgSize() {
            return isVerium ? VERIUM_MSGMAX : VERICOIN_MSGMAX;
        }

        const char* DaemonPidFileName() {
            return isVerium ? VERIUM_PID_FILENAME : VERICOIN_PID_FILENAME;
        }
}
