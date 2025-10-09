# DOCSIS Event Common

##

### CM STATUS

| CMSTATUS | Description                                                                                              |
| -------- | -------------------------------------------------------------------------------------------------------- |
| 0        | Reserved (no use)                                                                                        |
| 1        | Secondary Channel MDD Timeout (the MDD timer on a secondary channel expired)                             |
| 2        | QAM / FEC Lock Failure (loss of QAM or Forward Error Correction lock on downstream)                      |
| 3        | Sequence Out-of-Range (a packet sequence number was out of the expected range)                           |
| 4        | Secondary Channel MDD Recovery (receipt of MDD on a secondary channel)                                   |
| 5        | QAM / FEC Lock Recovery (channel regained lock)                                                          |
| 6        | T4 Timeout (station maintenance / broadcast failure)                                                     |
| 7        | T3 Retries Exceeded (ranging retries maximum exceeded)                                                   |
| 8        | Successful Ranging After T3 Retries Exceeded (ranging recovery)                                          |
| 9        | CM Operating on Battery Backup (loss of A/C power for > 5 seconds)                                       |
| 10       | CM Returned to A/C Power (came back from battery to A/C)                                                 |
| 11       | MAC Removal Event (one or more MAC addresses removed, e.g., in port transition)                          |
| 12–15    | Reserved for future use                                                                                  |
| 16       | DS OFDM Profile Failure (FEC errors exceeded limit on a downstream OFDM profile)                         |
| 17       | Primary Downstream Change (lost primary downstream, switched to backup)                                  |
| 18       | DPD Mismatch (Some mismatch in DPD change count vs NCP odd/even bit)                                     |
| 20       | NCP Profile Failure (FEC errors exceeded limit on NCP profile)                                           |
| 21       | PLC Failure (FEC errors exceeded on PLC)                                                                 |
| 22       | NCP Profile Recovery (FEC recovered on NCP)                                                              |
| 23       | PLC Recovery (FEC recovery on PLC channel)                                                               |
| 24       | OFDM Profile Recovery (FEC recovery on OFDM profile)                                                     |
| 25       | OFDMA Profile Failure (modem unable to support a received profile)                                       |
| 26       | MAP Storage Overflow (maps in CM overflow buffer)                                                        |
| 27       | MAP Storage Almost Full                                                                                  |
| 28–255   | Reserved / for vendor extensions                                                                         |
