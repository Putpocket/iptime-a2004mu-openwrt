# Performance and optimization

## Current measurements

On the hardware-tested image, traffic to or from the router itself reached
roughly 194–199 Mbit/s. The 1 GHz MIPS CPU was near saturation, and changing
MSS indicated a packet-rate rather than byte-rate limit.

This does not measure LAN-to-LAN hardware switching. All five external ports
negotiate at 1 Gbit/s full duplex, but link speed is not a throughput result.
LAN-to-LAN and WAN forwarding require two independent endpoints.

With the 5 GHz AP running and no associated station, a read-only snapshot
showed about 55.9 MiB total RAM, 4.8 MiB available RAM, and 21.7 MiB
unreclaimable slab. The kernel does not expose `/proc/slabinfo`, so the slab
owner is not yet proven.

## Low-risk optimization order

1. Measure LAN-to-LAN with two wired clients and simultaneous CPU/IRQ counters.
2. Measure WAN-to-LAN routing before and after OpenWrt software flow offload,
   using the same traffic and firewall configuration.
3. Compare memory with the 5 GHz radio disabled, then enabled without a
   station, then associated under load.
4. The publication config now omits `MAC80211_DEBUGFS` and mesh support.
   Compare its image size, memory, radio stability, and throughput with the
   hardware-tested diagnostic build.
5. Only after profiles identify driver cost, evaluate NAPI batching or
   descriptor-ring changes.

## Changes deliberately not made

- No vendor HWNAT import: it is high-risk, tightly coupled to old SDK code, and
  has unresolved licensing/provenance concerns.
- No checksum-offload work: controlled tests did not show it as the bottleneck.
- No untested IRQ, DMA, or ring tuning: the interrupt-driven path is currently
  the strongest stability result.
- No claim of gigabit forwarding until it is measured.
